from collections import Counter, defaultdict
from typing import List
import json
import logging
import os
import re
import tempfile
import unicodedata
from urllib.parse import urlparse

import bs4
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    WebBaseLoader,
)
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
try:
    import jieba
except Exception:
    jieba = None

from ..utils import generate_id, now_iso
from .langchain_client import get_chat_model, get_embeddings, get_reranker


_DOCUMENT_STORE: dict[str, list[dict]] = defaultdict(list)
_CHUNK_STORE: dict[str, list[dict]] = defaultdict(list)
_VECTOR_STORE_CACHE: dict[str, Chroma] = {}
_BM25_CACHE: dict[str, dict] = {}
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_INDEX_ROOT = os.path.join(_PROJECT_ROOT, "data", "knowledge-base", "indexes")
_logger = logging.getLogger(__name__)
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HEADING_NUMBER_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$")
_HEADING_CN_PATTERN = re.compile(r"^([一二三四五六七八九十]+)、\s*(.+)$")
_HEADING_PAREN_PATTERN = re.compile(r"^[（(]?\d+[）)]\s+(.+)$")
_MARKDOWN_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
_CODE_LINE_PATTERN = re.compile(r"^\s*(from|import|def|class|if|for|while|with)\b")
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]")
_ASCII_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")
_QUESTION_LINE_PATTERN = re.compile(r"(?:\?$|？$)")
_LIST_LINE_PATTERN = re.compile(r"^(\d+[\.\、]|[-•*])\s+")
_NUMERIC_PATTERN = re.compile(r"^\d+(\.\d+)?$")
_STOPWORDS = {
    "the",
    "and",
    "or",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "about",
    "also",
    "can",
    "will",
    "have",
    "has",
    "are",
    "was",
    "were",
    "is",
    "be",
    "to",
    "of",
    "in",
    "on",
    "a",
    "an",
    "the",
    "是",
    "的",
    "了",
    "和",
    "与",
    "及",
    "或",
    "以及",
    "一个",
    "一些",
    "这些",
    "那些",
    "我们",
    "你们",
    "他们",
    "可以",
    "需要",
    "进行",
    "包括",
    "主要",
    "相关",
    "用于",
}


def list_documents(course_id: str) -> list[dict]:
    _load_indexes(course_id)
    return list(_DOCUMENT_STORE.get(course_id, []))


def list_document_chunks(course_id: str, doc_id: str) -> list[dict]:
    _load_indexes(course_id)
    chunks = _CHUNK_STORE.get(course_id, [])
    return [chunk for chunk in chunks if chunk.get("source_doc_id") == doc_id]


def _normalize_doc_type(value: str) -> str:
    cleaned = value.strip().lower()
    return cleaned or "unknown"


def _tokenize_text(text: str) -> list[str]:
    raw = text or ""
    if not raw.strip():
        return []
    tokens: list[str] = []
    for segment in re.split(r"\s+", raw.strip()):
        if not segment:
            continue
        if re.search(r"[\u4e00-\u9fff]", segment) and jieba:
            tokens.extend([item for item in jieba.lcut(segment) if item.strip()])
        else:
            tokens.extend(_ASCII_TOKEN_PATTERN.findall(segment))
    return [token.lower() if token.isascii() else token for token in tokens if token.strip()]


def _is_valid_keyword(token: str) -> bool:
    if not token or not token.strip():
        return False
    cleaned = token.strip()
    if _NUMERIC_PATTERN.match(cleaned):
        return False
    if cleaned.lower() in _STOPWORDS:
        return False
    if cleaned.isascii() and len(cleaned) < 3:
        return False
    if not cleaned.isascii() and len(cleaned) < 2:
        return False
    return True


def _parse_csv_env(name: str) -> set[str]:
    value = os.getenv(name, "")
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item and item.strip()}


def _should_use_qa_split(course_id: str, doc_type: str) -> bool:
    enabled = os.getenv("RAG_QA_CHUNK_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
    }
    if not enabled:
        return False
    disabled_courses = _parse_csv_env("RAG_QA_CHUNK_DISABLED_COURSES")
    enabled_courses = _parse_csv_env("RAG_QA_CHUNK_COURSES")
    disabled_types = {item.lower() for item in _parse_csv_env("RAG_QA_CHUNK_DISABLED_DOCTYPES")}
    enabled_types = {item.lower() for item in _parse_csv_env("RAG_QA_CHUNK_DOCTYPES")}

    if course_id in disabled_courses:
        return False
    if enabled_courses and course_id in enabled_courses:
        return True

    normalized_type = (doc_type or "").strip().lower()
    if normalized_type in disabled_types:
        return False
    if enabled_types:
        return normalized_type in enabled_types
    return True


def _should_use_llm_chunking(course_id: str, doc_type: str, override: bool | None = None) -> bool:
    if override is not None:
        return override
    enabled = os.getenv("RAG_LLM_CHUNK_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
    }
    if not enabled:
        return False
    disabled_courses = _parse_csv_env("RAG_LLM_CHUNK_DISABLED_COURSES")
    enabled_courses = _parse_csv_env("RAG_LLM_CHUNK_COURSES")
    disabled_types = {item.lower() for item in _parse_csv_env("RAG_LLM_CHUNK_DISABLED_DOCTYPES")}
    enabled_types = {item.lower() for item in _parse_csv_env("RAG_LLM_CHUNK_DOCTYPES")}

    if course_id in disabled_courses:
        return False
    if enabled_courses and course_id in enabled_courses:
        return True

    normalized_type = (doc_type or "").strip().lower()
    if normalized_type in disabled_types:
        return False
    if enabled_types:
        return normalized_type in enabled_types
    return True


def _clear_bm25_cache(course_id: str) -> None:
    _BM25_CACHE.pop(course_id, None)


def _get_bm25_index(course_id: str) -> dict | None:
    cached = _BM25_CACHE.get(course_id)
    if cached:
        return cached
    chunks = list(_CHUNK_STORE.get(course_id, []))
    if not chunks:
        return None
    corpus_tokens = [_tokenize_text(chunk.get("content", "")) for chunk in chunks]
    bm25 = BM25Okapi(corpus_tokens)
    payload = {"bm25": bm25, "chunk_ids": [chunk.get("chunk_id") for chunk in chunks]}
    _BM25_CACHE[course_id] = payload
    return payload


def _build_chunk(course_id: str, document: dict) -> dict:
    chunk_id = generate_id("chunk")
    title_path = f"{document['name']} > 摘要"
    content = (
        f"文档《{document['name']}》的核心要点占位摘要，"
        f"用于演示检索与问答流程。"
    )
    return {
        "chunk_id": chunk_id,
        "course_id": course_id,
        "source_doc_id": document["id"],
        "source_doc_name": document["name"],
        "source_doc_type": document["doc_type"],
        "title_path": title_path,
        "content": content,
        "order_index": 1,
        "char_count": len(content),
    }


def _normalize_lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [_CONTROL_CHAR_PATTERN.sub("", line.rstrip()) for line in normalized.split("\n")]


def _normalize_text_content(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\u00a0", " ").replace("\u200b", "")
    normalized = re.sub(r"[ \t]{2,}", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _strip_repeated_lines(page_texts: list[str]) -> list[str]:
    if not page_texts:
        return page_texts
    lines_by_page = [_normalize_lines(text) for text in page_texts]
    normalized_counts: dict[str, int] = defaultdict(int)
    total_pages = len(lines_by_page)
    max_line_len = 50
    for lines in lines_by_page:
        seen: set[str] = set()
        for line in lines:
            normalized = re.sub(r"\s+", " ", line).strip()
            if not normalized or len(normalized) > max_line_len:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            normalized_counts[normalized] += 1
    threshold = max(2, int(total_pages * 0.6))
    repeated = {line for line, count in normalized_counts.items() if count >= threshold}
    noise_patterns = [
        re.compile(r"^扫码", re.IGNORECASE),
        re.compile(r"^知识星球", re.IGNORECASE),
        re.compile(r"^第?\s*\d+\s*页$", re.IGNORECASE),
    ]

    def is_noise(line: str) -> bool:
        normalized = re.sub(r"\s+", " ", line).strip()
        if not normalized:
            return True
        if normalized in repeated:
            return True
        return any(pattern.search(normalized) for pattern in noise_patterns)

    cleaned_pages: list[str] = []
    for lines in lines_by_page:
        kept = [line for line in lines if not is_noise(line)]
        cleaned_pages.append("\n".join(kept).strip())
    return cleaned_pages


def _merge_broken_lines(text: str) -> str:
    cjk_pattern = re.compile(r"[\u4e00-\u9fff]")
    block_start_pattern = re.compile(
        r"^(#+\s+|\d+(\.\d+)*\s+|[一二三四五六七八九十]+、|[（(]?\d+[）)]\s+|[•\-*]\s+)"
    )
    lines = _normalize_lines(text)
    blocks: list[str] = []
    buffer = ""

    def is_inline_noise(value: str) -> bool:
        if not value:
            return True
        if len(value) <= 20 and ("扫码" in value or "知识星球" in value or value == "查看更多"):
            return True
        return False

    def is_block_start(value: str) -> bool:
        if block_start_pattern.match(value):
            return True
        if len(value) <= 40 and value.endswith(("：", ":")):
            return True
        return False

    def flush() -> None:
        nonlocal buffer
        if buffer:
            blocks.append(buffer.strip())
            buffer = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if is_inline_noise(stripped):
            flush()
            continue
        if is_block_start(stripped):
            flush()
            buffer = stripped
            continue
        if not buffer:
            buffer = stripped
            continue
        if buffer.endswith("-") and stripped[:1].islower():
            buffer = buffer[:-1] + stripped
            continue
        if buffer[-1:] in "。！？!?；;":
            flush()
            buffer = stripped
            continue
        buffer_last = buffer[-1:]
        next_first = stripped[:1]
        if cjk_pattern.search(buffer_last) and (cjk_pattern.search(next_first) or next_first.isalnum()):
            buffer = f"{buffer}{stripped}"
            continue
        if buffer_last.isalnum() and next_first.isalnum():
            buffer = f"{buffer} {stripped}"
            continue
        flush()
        buffer = stripped

    flush()
    return "\n\n".join(line for line in blocks if line.strip())


def _fix_pdf_word_breaks(content: str) -> str:
    content = content.replace("\u00ad", "")
    content = re.sub(r"(\w)-\s+(\w)", r"\1\2", content)
    content = re.sub(r"\b([A-Za-z])\s+([a-z]{2,})\b", r"\1\2", content)
    content = re.sub(r"\b([A-Za-z]{2,})\s+([a-z]{2,})\b", r"\1\2", content)
    content = re.sub(r"\b([A-Za-z]+)'s\s+([a-z]{2,})\b", r"\1's\2", content)
    content = re.sub(r"\b([a-z])\s+([A-Za-z]{2,})\b", r"\1\2", content)
    content = re.sub(r"\b(a|an|the)\s+([a-z]{2,})\b", r"\1\2", content, flags=re.IGNORECASE)
    content = re.sub(
        r"\b([A-Z][a-z]+)(is|are|was|were|the|and|or|to|for|of|in|on|with)\b",
        r"\1 \2",
        content,
    )
    content = re.sub(r"(?<=[A-Za-z])\s{1,2}(?=[A-Za-z])", "", content)
    content = re.sub(r"(?<=[A-Za-z])\s{1,2}(?=\d)", "", content)
    content = re.sub(r"(?<=\d)\s{1,2}(?=[A-Za-z])", "", content)
    return content


def _merge_table_lines(content: str) -> str:
    lines = content.splitlines()
    merged: list[str] = []
    in_table = False
    table_lines: list[str] = []

    def flush_table() -> None:
        nonlocal table_lines, in_table
        if table_lines:
            merged.append("\n".join(table_lines).strip())
            table_lines = []
        in_table = False

    for line in lines:
        stripped = line.strip()
        is_table_line = "|" in stripped or bool(re.match(r"^[\s\-\|:]+$", stripped))
        if is_table_line:
            in_table = True
            table_lines.append(stripped)
            continue
        if in_table:
            flush_table()
        merged.append(line)
    if in_table:
        flush_table()
    return "\n".join(merged)


def _strip_toc_blocks(content: str) -> str:
    lines = content.splitlines()
    cleaned: list[str] = []
    buffer: list[str] = []
    toc_pattern = re.compile(r"^(•|\d+(\.\d+)*\s+)\S")

    def flush_buffer() -> None:
        nonlocal buffer
        if not buffer:
            return
        total = len(buffer)
        toc_hits = 0
        for item in buffer:
            stripped = item.strip()
            if stripped and len(stripped) <= 80 and toc_pattern.match(stripped):
                toc_hits += 1
        if total >= 5 and toc_hits / total >= 0.6:
            buffer = []
            return
        cleaned.extend(buffer)
        buffer = []

    for line in lines:
        if not line.strip():
            flush_buffer()
            cleaned.append(line)
            continue
        buffer.append(line)
    flush_buffer()
    return "\n".join(cleaned)


def _clean_pdf_text(page_texts: list[str]) -> str:
    cleaned_pages = _strip_repeated_lines(page_texts)
    merged_pages = [_merge_broken_lines(page) for page in cleaned_pages]
    content = "\n\n".join(page for page in merged_pages if page.strip())
    content = _CONTROL_CHAR_PATTERN.sub("", content)
    content = _fix_pdf_word_breaks(content)
    content = _merge_table_lines(content)
    content = _strip_toc_blocks(content)
    content = _normalize_text_content(content)
    content = re.sub(r"(扫码加查看更多|扫码查看更多|扫码查看|扫码加|知识星球)", "", content)
    content = re.sub(r"\n([•\-*]\s+)", "\n\n\\1", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def _merge_short_tail(chunks: list[str], min_len: int) -> list[str]:
    if not chunks:
        return []
    if len(chunks[-1]) >= min_len:
        return chunks
    if len(chunks) == 1:
        return chunks
    merged = chunks[:-2]
    merged.append(f"{chunks[-2]}\n\n{chunks[-1]}".strip())
    return merged


def _merge_short_payloads(payloads: list[dict], min_len: int) -> list[dict]:
    if not payloads:
        return []
    if len(payloads[-1].get("text", "")) >= min_len:
        return payloads
    if len(payloads) == 1:
        return payloads
    payloads[-2]["text"] = f"{payloads[-2]['text']}\n\n{payloads[-1]['text']}".strip()
    payloads.pop()
    return payloads


def _summarize_chunks_for_llm(chunks: list[dict], limit: int = 8) -> str:
    sorted_chunks = sorted(
        chunks,
        key=lambda item: item.get("char_count") if isinstance(item.get("char_count"), int) else 0,
        reverse=True,
    )
    lines: list[str] = []
    for chunk in sorted_chunks[:limit]:
        title = chunk.get("title_path", "")
        content = (chunk.get("content", "") or "").strip()
        if not content:
            continue
        excerpt = content[:300].strip()
        lines.append(f"{title}\n{excerpt}")
    return "\n\n".join(lines)


def _extract_keywords_from_chunks(chunks: list[dict], limit: int) -> list[str]:
    if not chunks:
        return []
    term_counts: Counter = Counter()
    doc_counts: Counter = Counter()
    for chunk in chunks:
        combined = f"{chunk.get('title_path', '')}\n{chunk.get('content', '')}"
        tokens = [token for token in _tokenize_text(combined) if _is_valid_keyword(token)]
        if not tokens:
            continue
        term_counts.update(tokens)
        doc_counts.update(set(tokens))
    if not term_counts:
        return []
    scored = []
    total_chunks = max(1, len(chunks))
    for term, freq in term_counts.items():
        doc_freq = doc_counts.get(term, 0)
        score = freq * (1.0 + (doc_freq / total_chunks))
        scored.append((term, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return [term for term, _ in scored[:limit]]


def _llm_generate_knowledge_points(
    course_id: str,
    chunks: list[dict],
    limit: int,
    use_llm: bool | None = None,
) -> list[str]:
    if use_llm is False:
        return []
    llm = get_chat_model()
    if not llm:
        return []
    max_input = int(os.getenv("RAG_LLM_KP_MAX_INPUT", "6000"))
    context = _summarize_chunks_for_llm(chunks, limit=8)
    if not context or len(context) > max_input:
        return []
    prompt = (
        "你是教学助理，请根据课程资料提炼关键知识点。\n"
        "要求：\n"
        f"- 返回 {limit} 个以内的知识点，使用短语，不要句子。\n"
        "- 优先提取概念、方法、原理、步骤、易考点。\n"
        "- 输出严格 JSON，不要包含多余说明。\n"
        "输出格式示例：\n"
        '["知识点1","知识点2"]\n'
        f"课程ID：{course_id}\n"
        "资料摘要：\n"
        f"{context}\n"
    )
    try:
        response = llm.invoke(prompt)
    except Exception:
        _logger.exception("LLM knowledge points generation failed for %s", course_id)
        return []
    raw_text = getattr(response, "content", response)
    parsed = _safe_json_load(str(raw_text))
    if isinstance(parsed, dict):
        payload = parsed.get("knowledge_points") or parsed.get("points")
    else:
        payload = parsed
    if not isinstance(payload, list):
        return []
    normalized = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized[:limit]


def generate_knowledge_points(
    course_id: str,
    limit: int = 12,
    use_llm: bool | None = None,
) -> list[str]:
    _load_indexes(course_id)
    chunks = list(_CHUNK_STORE.get(course_id, []))
    if not chunks:
        return []
    if limit < 1:
        return []
    llm_points = _llm_generate_knowledge_points(course_id, chunks, limit, use_llm=use_llm)
    if llm_points:
        return llm_points[:limit]
    return _extract_keywords_from_chunks(chunks, limit)


def _infer_heading_level(line: str) -> tuple[int, str] | None:
    markdown_match = _MARKDOWN_HEADING_PATTERN.match(line)
    if markdown_match:
        return len(markdown_match.group(1)), markdown_match.group(2).strip()
    number_match = _HEADING_NUMBER_PATTERN.match(line)
    if number_match:
        level = number_match.group(1).count(".") + 1
        return level, number_match.group(2).strip()
    cn_match = _HEADING_CN_PATTERN.match(line)
    if cn_match:
        return 1, cn_match.group(2).strip()
    paren_match = _HEADING_PAREN_PATTERN.match(line)
    if paren_match:
        return 2, paren_match.group(1).strip()
    if len(line) <= 40 and line.endswith(("：", ":")):
        return 3, line.rstrip("：:").strip()
    return None


def _compose_title_path(doc_name: str, stack: list[str]) -> str:
    safe_name = doc_name.strip() if isinstance(doc_name, str) else ""
    if not safe_name:
        safe_name = "文档"
    if not stack:
        return safe_name
    return f"{safe_name} > " + " > ".join(stack)


def _sanitize_title(value: str, max_len: int = 40) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip())
    if len(cleaned) > max_len:
        return cleaned[:max_len].rstrip() + "..."
    return cleaned or "未命名"


def _is_question_line(line: str) -> bool:
    if not line:
        return False
    if _QUESTION_LINE_PATTERN.search(line.strip()):
        return True
    return line.strip().endswith(("?", "？"))


def _detect_qa_mode(lines: list[str], course_id: str, doc_type: str) -> bool:
    if not _should_use_qa_split(course_id, doc_type):
        return False
    question_lines = [line for line in lines if _is_question_line(line)]
    if len(question_lines) < 3:
        return False
    return len(question_lines) >= max(2, int(len(lines) * 0.05))


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*", "", cleaned).strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[: cleaned.rfind("```")].strip()
    return cleaned


def _safe_json_load(text: str) -> list[dict] | dict | None:
    if not text:
        return None
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except Exception:
            return None
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except Exception:
            return None
    return None


def _normalize_llm_payloads(
    payloads: list[dict],
    doc_name: str,
    min_len: int,
    max_len: int,
) -> list[dict]:
    normalized: list[dict] = []
    for payload in payloads:
        text = _normalize_text_content(payload.get("text", ""))
        title_path = payload.get("title_path") or doc_name
        if not text:
            continue
        if len(text) > max_len:
            pieces = _split_long_text(text, max_len)
            normalized.extend(
                {"text": piece, "title_path": title_path} for piece in pieces if piece.strip()
            )
            continue
        normalized.append({"text": text, "title_path": title_path})
    return _merge_short_payloads(normalized, min_len)


def _llm_chunk_text(
    content: str,
    doc_name: str,
    course_id: str,
    doc_type: str,
    min_len: int,
    max_len: int,
    qa_mode: bool,
    override: bool | None = None,
) -> list[dict]:
    if not _should_use_llm_chunking(course_id, doc_type, override=override):
        return []
    chat_model = get_chat_model()
    if not chat_model:
        return []
    max_input = int(os.getenv("RAG_LLM_CHUNK_MAX_INPUT", "6000"))
    if len(content) > max_input:
        return []

    mode_hint = "问答" if qa_mode else "通用"
    prompt = (
        "你是中文文档切分助手。请根据输入内容生成语义连贯的片段列表。\n"
        "要求：\n"
        f"- 模式：{mode_hint}\n"
        f"- 每个片段长度在 {min_len}-{max_len} 字符之间，过长需拆分，过短需合并。\n"
        "- 保留代码块和表格为完整片段，不要打断。\n"
        "- title_path 使用层级标题路径，不确定时仅使用文档名。\n"
        "- 输出严格 JSON，不要包含多余说明。\n"
        "输出格式示例：\n"
        '{"chunks":[{"title_path":"文档名 > 章节","text":"..."}]}\n'
        f"文档名：{doc_name}\n"
        "正文如下：\n"
        f"{content}\n"
    )
    try:
        response = chat_model.invoke(prompt)
    except Exception:
        _logger.exception("LLM chunking failed for %s", doc_name)
        return []

    raw_text = getattr(response, "content", response)
    parsed = _safe_json_load(str(raw_text))
    if not parsed:
        return []
    if isinstance(parsed, dict):
        payloads = parsed.get("chunks")
    else:
        payloads = parsed
    if not isinstance(payloads, list):
        return []
    normalized = _normalize_llm_payloads(payloads, doc_name, min_len, max_len)
    return normalized


def _maybe_split_list_blocks(text: str, max_items: int = 6) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    list_lines = [line for line in lines if _LIST_LINE_PATTERN.match(line.strip())]
    if len(list_lines) < max_items + 2:
        return [text.strip()]
    blocks: list[str] = []
    buffer: list[str] = []
    list_count = 0
    for line in lines:
        buffer.append(line)
        if _LIST_LINE_PATTERN.match(line.strip()):
            list_count += 1
            if list_count >= max_items:
                blocks.append("\n".join(buffer).strip())
                buffer = []
                list_count = 0
    if buffer:
        blocks.append("\n".join(buffer).strip())
    return [block for block in blocks if block]


def _dedupe_blocks(blocks: list[dict]) -> list[dict]:
    if not blocks:
        return []
    deduped: list[dict] = [blocks[0]]
    for current in blocks[1:]:
        prev = deduped[-1]
        prev_text = re.sub(r"\s+", " ", prev["text"]).strip()
        curr_text = re.sub(r"\s+", " ", current["text"]).strip()
        if not prev_text or not curr_text:
            deduped.append(current)
            continue
        if prev_text == curr_text or curr_text in prev_text or prev_text in curr_text:
            if len(curr_text) > len(prev_text):
                deduped[-1] = current
            continue
        prev_tokens = set(_TOKEN_PATTERN.findall(prev_text))
        curr_tokens = set(_TOKEN_PATTERN.findall(curr_text))
        if prev_tokens and curr_tokens:
            similarity = len(prev_tokens & curr_tokens) / max(1, len(prev_tokens | curr_tokens))
            if similarity >= 0.9:
                if len(curr_text) > len(prev_text):
                    deduped[-1] = current
                continue
        deduped.append(current)
    return deduped


def _is_table_block(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    table_like = sum(1 for line in lines if "|" in line or re.match(r"^[\s\-\|:]+$", line))
    return table_like >= 2


def _is_code_block(text: str) -> bool:
    for line in text.splitlines():
        if "```" in line:
            return True
        if _CODE_LINE_PATTERN.match(line):
            return True
    return False


def _split_long_text(text: str, max_len: int) -> list[str]:
    if len(text) <= max_len:
        return [text]
    sentence_splitter = re.compile(r"(?<=[。！？!?；;])\s+|(?<=[.!?])\s+(?=[A-Z0-9])")
    sentences = [item.strip() for item in sentence_splitter.split(text) if item.strip()]
    if not sentences:
        return [text]
    chunks: list[str] = []
    buffer = ""
    for sentence in sentences:
        if not buffer:
            buffer = sentence
            continue
        if len(buffer) + len(sentence) + 1 <= max_len:
            buffer = f"{buffer} {sentence}".strip()
            continue
        chunks.append(buffer)
        buffer = sentence
    if buffer:
        chunks.append(buffer)
    return chunks


def _extract_overlap(text: str, max_len: int) -> str:
    sentence_splitter = re.compile(r"(?<=[。！？!?；;])\s+|(?<=[.!?])\s+(?=[A-Z0-9])")
    sentences = [item.strip() for item in sentence_splitter.split(text) if item.strip()]
    if not sentences:
        return text[-max_len:]
    overlap: list[str] = []
    current_len = 0
    for sentence in reversed(sentences):
        if current_len + len(sentence) + 1 > max_len and overlap:
            break
        overlap.append(sentence)
        current_len += len(sentence) + 1
    return " ".join(reversed(overlap)).strip()


def _split_text_into_chunks(
    content: str,
    doc_name: str,
    course_id: str,
    doc_type: str,
    min_len: int = 80,
    max_len: int = 600,
    overlap: int = 60,
) -> list[dict]:
    lines = [line for line in content.splitlines()]
    blocks: list[dict] = []
    buffer: list[str] = []
    heading_stack: list[str] = []
    qa_mode = _detect_qa_mode(lines, course_id, doc_type)

    def flush_buffer() -> None:
        if not buffer:
            return
        text = "\n".join(buffer).strip()
        if text:
            blocks.append(
                {
                    "text": text,
                    "title_path": _compose_title_path(doc_name, heading_stack),
                }
            )
        buffer.clear()

    if qa_mode:
        qa_stack_prefix = ["问答"]
        current_question: str | None = None
        answer_lines: list[str] = []

        def flush_qa() -> None:
            nonlocal current_question, answer_lines
            if not current_question:
                return
            answer_text = "\n".join(answer_lines).strip()
            if answer_text:
                answer_blocks = _maybe_split_list_blocks(answer_text, max_items=6)
                for answer_block in answer_blocks:
                    blocks.append(
                        {
                            "text": answer_block,
                            "title_path": _compose_title_path(
                                doc_name,
                                qa_stack_prefix + [_sanitize_title(current_question)],
                            ),
                        }
                    )
            current_question = None
            answer_lines = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                if current_question:
                    answer_lines.append("")
                continue
            if _is_question_line(line):
                flush_qa()
                current_question = line
                continue
            if current_question:
                answer_lines.append(line)
            else:
                buffer.append(line)
        flush_qa()
        flush_buffer()
    else:
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                flush_buffer()
                continue
            heading_info = _infer_heading_level(line)
            if heading_info:
                flush_buffer()
                level, title = heading_info
                while len(heading_stack) >= level:
                    heading_stack.pop()
                heading_stack.append(title)
                buffer.append(line)
                continue
            buffer.append(line)
        flush_buffer()

    chunk_payloads: list[dict] = []
    current_chunks: list[str] = []
    current_len = 0
    current_title = ""

    def finalize_chunk() -> None:
        nonlocal current_chunks, current_len, current_title
        if not current_chunks:
            return
        text = "\n\n".join(current_chunks).strip()
        if text:
            chunk_payloads.append({"text": text, "title_path": current_title})
        current_chunks = []
        current_len = 0
        current_title = ""

    blocks = _dedupe_blocks(blocks)
    if qa_mode:
        min_len = 200
        max_len = 400
        overlap = 40

    for block in blocks:
        block_text = block["text"]
        block_title = block["title_path"]
        block_type = "paragraph"
        if _is_table_block(block_text):
            block_type = "table"
        elif _is_code_block(block_text):
            block_type = "code"
        block_max_len = 1000 if block_type in {"table", "code"} else max_len
        block_pieces = _split_long_text(block_text, block_max_len)

        for piece in block_pieces:
            if current_title and block_title != current_title and current_len >= min_len:
                finalize_chunk()
            if (
                current_chunks
                and current_len + len(piece) + 2 > max_len
                and current_len >= min_len
            ):
                finalize_chunk()
                if chunk_payloads and block_title == chunk_payloads[-1]["title_path"]:
                    overlap_text = _extract_overlap(chunk_payloads[-1]["text"], overlap)
                    if overlap_text:
                        current_chunks.append(overlap_text)
                        current_len += len(overlap_text)
            if not current_chunks:
                current_title = block_title
            current_chunks.append(piece)
            current_len += len(piece)
    finalize_chunk()

    if len(chunk_payloads) >= 2 and len(chunk_payloads[-1]["text"]) < min_len:
        chunk_payloads[-2]["text"] = (
            f"{chunk_payloads[-2]['text']}\n\n{chunk_payloads[-1]['text']}".strip()
        )
        chunk_payloads.pop()

    return chunk_payloads


def _build_chunks(
    course_id: str, document: dict, content: str, use_llm_chunking: bool | None = None
) -> list[dict]:
    cleaned = _normalize_text_content(content)
    if not cleaned:
        return [_build_chunk(course_id, document)]

    doc_type = document.get("doc_type", "")
    lines = cleaned.splitlines()
    qa_mode = _detect_qa_mode(lines, course_id, doc_type)
    min_len = 200 if qa_mode else 80
    max_len = 400 if qa_mode else 600

    chunks: list[dict] = []
    payloads = _split_text_into_chunks(
        cleaned,
        document["name"],
        course_id,
        doc_type,
        min_len=min_len,
        max_len=max_len,
    )
    llm_payloads = _llm_chunk_text(
        cleaned,
        document["name"],
        course_id,
        doc_type,
        min_len=min_len,
        max_len=max_len,
        qa_mode=qa_mode,
        override=use_llm_chunking,
    )
    if llm_payloads:
        payloads = llm_payloads
    if not payloads:
        payloads = [{"text": cleaned, "title_path": document["name"]}]
    for index, payload in enumerate(payloads, start=1):
        text = payload["text"]
        chunk_id = generate_id("chunk")
        chunks.append(
            {
                "chunk_id": chunk_id,
                "course_id": course_id,
                "source_doc_id": document["id"],
                "source_doc_name": document["name"],
                "source_doc_type": document["doc_type"],
                "title_path": f"{payload['title_path']} > 片段 {index}",
                "content": text,
                "order_index": index,
                "char_count": len(text),
            }
        )

    return chunks or [_build_chunk(course_id, document)]


def _infer_doc_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    return ext or "unknown"


def _load_with_langchain(filename: str, data: bytes) -> list[str]:
    ext = os.path.splitext(filename)[1].lower()
    suffix = ext or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name
    try:
        if ext == ".pdf":
            loader = PyPDFLoader(tmp_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(tmp_path)
        else:
            loader = TextLoader(tmp_path, encoding="utf-8")
        documents = loader.load()
        return [doc.page_content for doc in documents if doc.page_content]
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _extract_text(filename: str, data: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".md", ".markdown", ".txt"}:
        try:
            contents = _load_with_langchain(filename, data)
            text = "\n".join(contents).strip()
        except Exception:
            text = data.decode("utf-8", errors="ignore")
        if not text.strip():
            _logger.warning("Extracted empty text from %s", filename)
        return text
    if ext == ".pdf":
        try:
            page_texts = _load_with_langchain(filename, data)
            text = _clean_pdf_text(page_texts)
            if not text.strip():
                _logger.warning("Extracted empty text from PDF %s", filename)
            return text
        except Exception:
            _logger.exception("Failed to extract PDF text from %s", filename)
            return ""
    if ext == ".docx":
        try:
            contents = _load_with_langchain(filename, data)
            text = "\n".join(contents)
            if not text.strip():
                _logger.warning("Extracted empty text from DOCX %s", filename)
            return text
        except Exception:
            _logger.exception("Failed to extract DOCX text from %s", filename)
            return ""
    text = data.decode("utf-8", errors="ignore")
    if not text.strip():
        _logger.warning("Extracted empty text from %s", filename)
    return text


def store_documents(
    course_id: str, documents: List[dict], use_llm_chunking: bool | None = None
) -> list[dict]:
    _load_indexes(course_id)
    stored: list[dict] = []
    new_chunks: list[dict] = []
    for doc in documents:
        if doc.get("name"):
            _remove_documents(course_id, lambda item: item.get("name") == doc.get("name"))
        doc_type = _normalize_doc_type(doc.get("doc_type", "unknown"))
        entry = {
            "id": generate_id("doc"),
            "name": doc["name"],
            "doc_type": doc_type,
            "status": "indexed",
            "created_at": now_iso(),
        }
        stored.append(entry)
        chunk = _build_chunk(course_id, entry)
        _CHUNK_STORE[course_id].append(chunk)
        new_chunks.append(chunk)
    _DOCUMENT_STORE[course_id].extend(stored)
    _persist_indexes(course_id)
    _index_chunks(course_id, new_chunks)
    _clear_bm25_cache(course_id)
    return stored


def store_uploaded_documents(
    course_id: str, uploads: list[dict], use_llm_chunking: bool | None = None
) -> list[dict]:
    _load_indexes(course_id)
    stored: list[dict] = []
    new_chunks: list[dict] = []
    for upload in uploads:
        name = upload.get("name", "unknown")
        if name:
            _remove_documents(course_id, lambda item: item.get("name") == name)
        doc_type = _normalize_doc_type(upload.get("doc_type") or _infer_doc_type(name))
        content = upload.get("content", "")
        entry = {
            "id": generate_id("doc"),
            "name": name,
            "doc_type": doc_type,
            "status": "indexed",
            "created_at": now_iso(),
        }
        stored.append(entry)
        chunks = _build_chunks(course_id, entry, content, use_llm_chunking=use_llm_chunking)
        _CHUNK_STORE[course_id].extend(chunks)
        new_chunks.extend(chunks)
    _DOCUMENT_STORE[course_id].extend(stored)
    _persist_indexes(course_id)
    _index_chunks(course_id, new_chunks)
    _clear_bm25_cache(course_id)
    return stored


def extract_upload_payload(filename: str, data: bytes) -> dict:
    return {
        "name": filename,
        "doc_type": _infer_doc_type(filename),
        "content": _extract_text(filename, data),
    }


def _merge_chunks_content(chunks: list[dict]) -> str:
    sorted_chunks = sorted(
        chunks,
        key=lambda item: item.get("order_index") if isinstance(item.get("order_index"), int) else 0,
    )
    return "\n\n".join(chunk.get("content", "") for chunk in sorted_chunks).strip()


def update_document(
    course_id: str,
    doc_id: str,
    name: str | None = None,
    doc_type: str | None = None,
    content: str | None = None,
    use_llm_chunking: bool | None = None,
) -> dict | None:
    _load_indexes(course_id)
    documents = list(_DOCUMENT_STORE.get(course_id, []))
    current = next((doc for doc in documents if doc.get("id") == doc_id), None)
    if not current:
        return None
    existing_chunks = [
        chunk for chunk in _CHUNK_STORE.get(course_id, []) if chunk.get("source_doc_id") == doc_id
    ]
    if content is None:
        content = _merge_chunks_content(existing_chunks)
    updated_name = (name or current.get("name") or "").strip() or current.get("name", "unknown")
    updated_type = _normalize_doc_type(doc_type or current.get("doc_type") or "unknown")

    _remove_documents(course_id, lambda item: item.get("id") == doc_id)
    entry = {
        "id": doc_id,
        "name": updated_name,
        "doc_type": updated_type,
        "status": "indexed",
        "created_at": current.get("created_at") or now_iso(),
    }
    _DOCUMENT_STORE[course_id].append(entry)
    chunks = _build_chunks(course_id, entry, content or "", use_llm_chunking=use_llm_chunking)
    _CHUNK_STORE[course_id].extend(chunks)
    _persist_indexes(course_id)
    _index_chunks(course_id, chunks)
    _clear_bm25_cache(course_id)
    return entry


def _derive_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = (parsed.path or "").rstrip("/")
    last_segment = path.split("/")[-1] if path else ""
    if last_segment:
        return last_segment
    return parsed.netloc or url


def _build_web_bs_kwargs(parse_classes: list[str] | None) -> dict:
    if not parse_classes:
        return {}
    cleaned = [item.strip() for item in parse_classes if item and item.strip()]
    if not cleaned:
        return {}
    return {"parse_only": bs4.SoupStrainer(class_=tuple(cleaned))}


def extract_web_payload(url: str, parse_classes: list[str] | None = None) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("invalid url")
    bs_kwargs = _build_web_bs_kwargs(parse_classes)
    loader = WebBaseLoader(web_paths=[url], bs_kwargs=bs_kwargs or None)
    documents = loader.load()
    content_parts = [doc.page_content for doc in documents if doc.page_content]
    content = _normalize_text_content("\n\n".join(content_parts))
    title = None
    for doc in documents:
        metadata = doc.metadata or {}
        if metadata.get("title"):
            title = metadata["title"]
            break
    name = title or _derive_name_from_url(url)
    return {
        "name": name,
        "doc_type": "web",
        "content": content,
    }


def _remove_documents(course_id: str, predicate) -> list[dict]:
    docs = list(_DOCUMENT_STORE.get(course_id, []))
    if not docs:
        return []
    removed = [doc for doc in docs if predicate(doc)]
    if not removed:
        return []
    remaining = [doc for doc in docs if not predicate(doc)]
    removed_ids = {doc.get("id") for doc in removed if doc.get("id")}
    chunks = list(_CHUNK_STORE.get(course_id, []))
    removed_chunks = [
        chunk for chunk in chunks if chunk.get("source_doc_id") in removed_ids
    ]
    remaining_chunks = [
        chunk
        for chunk in chunks
        if chunk.get("source_doc_id") not in removed_ids
    ]
    _DOCUMENT_STORE[course_id] = remaining
    _CHUNK_STORE[course_id] = remaining_chunks
    _persist_indexes(course_id)
    _clear_bm25_cache(course_id)
    for doc in removed:
        doc_name = doc.get("name")
        doc_id = doc.get("id")
        if not doc_name or not doc_id:
            continue
        try:
            os.remove(_doc_chunks_path(course_id, doc_name, doc_id))
        except OSError:
            pass
    _delete_chunk_embeddings(
        course_id,
        [chunk.get("chunk_id") for chunk in removed_chunks if chunk.get("chunk_id")],
    )
    return removed


def delete_document(course_id: str, doc_id: str) -> bool:
    _load_indexes(course_id)
    removed = _remove_documents(course_id, lambda item: item.get("id") == doc_id)
    return bool(removed)


def search_documents(
    course_id: str,
    query: str,
    top_k: int,
    filters: dict | None = None,
) -> list[dict]:
    _load_indexes(course_id)
    if not query.strip():
        return []
    if not _CHUNK_STORE.get(course_id):
        return []

    rerank_enabled = os.getenv("RAG_RERANK_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
    }
    candidate_cap = int(os.getenv("RAG_RERANK_CANDIDATES", "20"))
    candidate_cap = max(candidate_cap, top_k)
    fetch_k = min(candidate_cap, max(top_k * 4, top_k))
    bm25_enabled = os.getenv("RAG_BM25_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
    }
    weight_vector = float(os.getenv("RAG_HYBRID_WEIGHT_VECTOR", "0.6"))
    weight_bm25 = float(os.getenv("RAG_HYBRID_WEIGHT_BM25", "0.4"))

    filter_payload = None
    allowed_types = None
    if filters and isinstance(filters, dict):
        allowed_types = filters.get("source_doc_type")
        if allowed_types:
            allowed_types = {item.strip().lower() for item in allowed_types if item}
            filter_payload = {"source_doc_type": {"$in": allowed_types}}

    store = _get_vector_store(course_id)
    try:
        raw_results = store.similarity_search_with_score(
            query,
            k=fetch_k,
            filter=filter_payload,
        )
    except TypeError:
        raw_results = store.similarity_search_with_score(query, k=fetch_k)

    chunk_lookup = {chunk.get("chunk_id"): chunk for chunk in _CHUNK_STORE.get(course_id, [])}
    vector_results: dict[str, dict] = {}
    for doc, score in raw_results:
        metadata = doc.metadata or {}
        chunk_id = metadata.get("chunk_id", "")
        if not chunk_id:
            continue
        vector_results[chunk_id] = {
            "chunk_id": chunk_id,
            "score": float(score) if score is not None else 0.0,
            "content": doc.page_content,
            "title_path": metadata.get("title_path", ""),
            "source_doc_id": metadata.get("source_doc_id", ""),
            "source_doc_name": metadata.get("source_doc_name", ""),
            "source_doc_type": metadata.get("source_doc_type", ""),
        }

    results_map: dict[str, dict] = {}
    for chunk_id, item in vector_results.items():
        results_map[chunk_id] = dict(item)

    bm25_pairs: list[tuple[str, float]] = []
    bm25_scores: dict[str, float] = {}
    if bm25_enabled:
        bm25_index = _get_bm25_index(course_id)
        query_tokens = _tokenize_text(query)
        if bm25_index and query_tokens:
            scores = bm25_index["bm25"].get_scores(query_tokens)
            for index, score in enumerate(scores):
                chunk_id = bm25_index["chunk_ids"][index]
                if not chunk_id:
                    continue
                chunk_meta = chunk_lookup.get(chunk_id)
                if not chunk_meta:
                    continue
                if allowed_types and chunk_meta.get("source_doc_type") not in allowed_types:
                    continue
                bm25_pairs.append((chunk_id, float(score)))
            bm25_pairs.sort(key=lambda item: item[1], reverse=True)
            bm25_pairs = bm25_pairs[:fetch_k]
            bm25_scores = {chunk_id: score for chunk_id, score in bm25_pairs}

    for chunk_id, score in bm25_scores.items():
        if chunk_id in results_map:
            results_map[chunk_id]["bm25_score"] = score
            continue
        chunk_meta = chunk_lookup.get(chunk_id)
        if not chunk_meta:
            continue
        results_map[chunk_id] = {
            "chunk_id": chunk_meta.get("chunk_id", ""),
            "score": 1.0,
            "content": chunk_meta.get("content", ""),
            "title_path": chunk_meta.get("title_path", ""),
            "source_doc_id": chunk_meta.get("source_doc_id", ""),
            "source_doc_name": chunk_meta.get("source_doc_name", ""),
            "source_doc_type": chunk_meta.get("source_doc_type", ""),
            "bm25_score": score,
        }

    results: list[dict] = list(results_map.values())

    if bm25_enabled and results:
        max_bm25 = max((item.get("bm25_score", 0.0) for item in results), default=0.0)
        vector_sims = [
            max(0.0, 1.0 - item.get("score", 1.0))
            for item in results
            if item.get("score") is not None
        ]
        max_vector_sim = max(vector_sims, default=0.0)
        for item in results:
            vector_sim = max(0.0, 1.0 - float(item.get("score", 1.0)))
            vector_norm = vector_sim / max_vector_sim if max_vector_sim > 0 else 0.0
            bm25_norm = (
                float(item.get("bm25_score", 0.0)) / max_bm25 if max_bm25 > 0 else 0.0
            )
            item["bm25_score"] = bm25_norm
            item["hybrid_score"] = weight_vector * vector_norm + weight_bm25 * bm25_norm

        results.sort(
            key=lambda item: float(item.get("hybrid_score", 0.0)),
            reverse=True,
        )

    if not rerank_enabled or len(results) <= 1:
        return results[:top_k]

    reranker = get_reranker()
    if not reranker:
        return results[:top_k]

    documents = [
        Document(
            page_content=item.get("content", ""),
            metadata={
                "chunk_id": item.get("chunk_id", ""),
                "title_path": item.get("title_path", ""),
                "source_doc_id": item.get("source_doc_id", ""),
                "source_doc_name": item.get("source_doc_name", ""),
                "vector_score": item.get("score", 0.0),
            },
        )
        for item in results
    ]
    try:
        rerank_items = reranker.rerank(documents, query, top_n=len(documents))
    except Exception:
        _logger.exception("Rerank failed, falling back to vector similarity results.")
        return results[:top_k]

    if not rerank_items:
        return results[:top_k]

    reranked: list[dict] = []
    for item in rerank_items:
        index = item.get("index")
        if not isinstance(index, int) or index < 0 or index >= len(results):
            continue
        entry = dict(results[index])
        entry["rerank_score"] = float(item.get("relevance_score", 0.0))
        reranked.append(entry)

    if not reranked:
        return results[:top_k]

    return reranked[:top_k]


def _get_course_title(course_id: str) -> str | None:
    try:
        from ..db import get_connection
    except Exception:
        return None
    conn = get_connection()
    row = conn.execute("SELECT title FROM courses WHERE id = ?", (course_id,)).fetchone()
    conn.close()
    if not row:
        return None
    title = row["title"] if isinstance(row, dict) else row[0]
    return title.strip() if isinstance(title, str) else None


def get_course_title(course_id: str) -> str | None:
    return _get_course_title(course_id)


def _safe_folder_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    cleaned = cleaned.replace(os.sep, "_")
    if os.altsep:
        cleaned = cleaned.replace(os.altsep, "_")
    cleaned = re.sub(r"[^\w\u4e00-\u9fff\-\s]", "_", cleaned, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or ""


def _legacy_course_dir(course_id: str) -> str:
    return os.path.join(_INDEX_ROOT, course_id)


def _course_dir(course_id: str) -> str:
    title = _get_course_title(course_id)
    folder_name = _safe_folder_name(title or "")
    if not folder_name:
        folder_name = course_id
    return os.path.join(_INDEX_ROOT, folder_name)


def _ensure_course_dir(course_id: str) -> str:
    path = _course_dir(course_id)
    os.makedirs(path, exist_ok=True)
    return path


def _vector_dir(course_id: str) -> str:
    return os.path.join(_course_dir(course_id), "chroma")


def _documents_path(course_id: str) -> str:
    return os.path.join(_course_dir(course_id), "documents.json")


def _chunks_dir(course_id: str) -> str:
    return os.path.join(_course_dir(course_id), "chunks")


def _doc_chunks_path(course_id: str, doc_name: str, doc_id: str) -> str:
    safe_name = _safe_folder_name(doc_name) or "unknown"
    safe_id = _safe_folder_name(doc_id) or "unknown"
    return os.path.join(_chunks_dir(course_id), f"{safe_name}__{safe_id}.json")


def _get_vector_store(course_id: str) -> Chroma:
    if course_id in _VECTOR_STORE_CACHE:
        return _VECTOR_STORE_CACHE[course_id]
    _ensure_course_dir(course_id)
    store = Chroma(
        collection_name=f"course_{course_id}",
        embedding_function=get_embeddings(),
        persist_directory=_vector_dir(course_id),
        collection_metadata={"hnsw:space": "cosine"},
    )
    _VECTOR_STORE_CACHE[course_id] = store
    return store


def _build_vector_documents(chunks: list[dict]) -> tuple[list[Document], list[str]]:
    documents: list[Document] = []
    ids: list[str] = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if not chunk_id:
            continue
        metadata = {
            "chunk_id": chunk_id,
            "course_id": chunk.get("course_id"),
            "source_doc_id": chunk.get("source_doc_id"),
            "source_doc_name": chunk.get("source_doc_name"),
            "source_doc_type": chunk.get("source_doc_type"),
            "title_path": chunk.get("title_path"),
            "order_index": chunk.get("order_index"),
            "char_count": chunk.get("char_count"),
        }
        cleaned_metadata = {key: value for key, value in metadata.items() if value is not None}
        cleaned_metadata = {
            key: value
            for key, value in cleaned_metadata.items()
            if isinstance(value, (str, int, float, bool))
        }
        documents.append(
            Document(page_content=chunk.get("content", ""), metadata=cleaned_metadata)
        )
        ids.append(chunk_id)
    return documents, ids


def _index_chunks(course_id: str, chunks: list[dict]) -> None:
    if not chunks:
        return
    store = _get_vector_store(course_id)
    documents, ids = _build_vector_documents(chunks)
    if not documents:
        return
    batch_size = 10
    for start in range(0, len(documents), batch_size):
        end = start + batch_size
        store.add_documents(documents[start:end], ids=ids[start:end])
    if hasattr(store, "persist"):
        store.persist()


def _delete_chunk_embeddings(course_id: str, chunk_ids: list[str]) -> None:
    if not chunk_ids:
        return
    store = _get_vector_store(course_id)
    store.delete(ids=chunk_ids)
    if hasattr(store, "persist"):
        store.persist()


def _load_json(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
            return payload if isinstance(payload, list) else []
    except Exception:
        return []


def _save_json(path: str, data: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _save_chunks_by_document(course_id: str) -> None:
    chunks = list(_CHUNK_STORE.get(course_id, []))
    os.makedirs(_chunks_dir(course_id), exist_ok=True)
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for chunk in chunks:
        doc_name = chunk.get("source_doc_name")
        doc_id = chunk.get("source_doc_id")
        if not doc_name or not doc_id:
            continue
        grouped[(doc_name, doc_id)].append(chunk)
    for (doc_name, doc_id), items in grouped.items():
        _save_json(_doc_chunks_path(course_id, doc_name, doc_id), items)


def _load_chunks_by_documents(course_id: str, documents: list[dict]) -> list[dict]:
    chunks: list[dict] = []
    for doc in documents:
        doc_name = doc.get("name")
        doc_id = doc.get("id")
        if not doc_name or not doc_id:
            continue
        chunks.extend(_load_json(_doc_chunks_path(course_id, doc_name, doc_id)))
    return chunks


def _sync_vector_store(course_id: str) -> None:
    chunks = list(_CHUNK_STORE.get(course_id, []))
    if not chunks:
        return
    store = _get_vector_store(course_id)
    try:
        existing = store.get(include=[])
        if existing.get("ids"):
            return
    except Exception:
        pass
    documents, ids = _build_vector_documents(chunks)
    if not documents:
        return
    batch_size = 10
    for start in range(0, len(documents), batch_size):
        end = start + batch_size
        store.add_documents(documents[start:end], ids=ids[start:end])
    if hasattr(store, "persist"):
        store.persist()


def _load_indexes(course_id: str) -> None:
    if _DOCUMENT_STORE.get(course_id) or _CHUNK_STORE.get(course_id):
        return
    new_path = _course_dir(course_id)
    legacy_path = _legacy_course_dir(course_id)
    if not os.path.exists(new_path) and os.path.exists(legacy_path):
        os.makedirs(_INDEX_ROOT, exist_ok=True)
        try:
            os.replace(legacy_path, new_path)
        except Exception:
            _logger.exception("Failed to migrate index folder for course %s", course_id)
    documents = _load_json(_documents_path(course_id))
    chunks = _load_chunks_by_documents(course_id, documents)
    if not chunks:
        legacy_chunks = _load_json(os.path.join(_course_dir(course_id), "chunks.json"))
        if legacy_chunks:
            chunks = legacy_chunks
            _CHUNK_STORE[course_id] = chunks
            _save_chunks_by_document(course_id)
            try:
                os.remove(os.path.join(_course_dir(course_id), "chunks.json"))
            except OSError:
                pass
    if documents:
        _DOCUMENT_STORE[course_id] = documents
    if chunks:
        _CHUNK_STORE[course_id] = chunks
        _sync_vector_store(course_id)


def _persist_indexes(course_id: str) -> None:
    _ensure_course_dir(course_id)
    _save_json(_documents_path(course_id), list(_DOCUMENT_STORE.get(course_id, [])))
    _save_chunks_by_document(course_id)
