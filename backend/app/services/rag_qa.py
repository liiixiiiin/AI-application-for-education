import json
import os
from typing import Any, Iterable

from dashscope import Assistants, Runs, Threads

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .knowledge_base import get_course_title, search_documents
from .langchain_client import get_chat_model, is_dashscope_configured


def _format_context(results: list[dict]) -> str:
    context_lines = []
    for idx, result in enumerate(results, start=1):
        source_name = result.get("source_doc_name", "unknown")
        source_id = result.get("source_doc_id", "")
        chunk_id = result.get("chunk_id", "")
        score = result.get("score")
        score_label = f"{score:.4f}" if isinstance(score, (int, float)) else "n/a"
        context_lines.append(
            "\n".join(
                [
                    f"[{idx}] {result.get('title_path', '')}",
                    f"来源: {source_name} ({source_id})",
                    f"片段ID: {chunk_id} | 相似度: {score_label}",
                    result.get("content", ""),
                ]
            )
        )
    return "\n\n".join(context_lines)


def _build_chain():
    if not is_dashscope_configured():
        return None
    llm = get_chat_model()
    if not llm:
        return None
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是教学问答助手。仅基于提供的检索内容回答问题，"
                "若材料不足则依据你自己的知识储备回答。",
            ),
            (
                "user",
                "课程：{course_name}\n问题：{question}\n\n检索资料：\n{context}\n\n回答：",
            ),
        ]
    )
    return prompt | llm | StrOutputParser()


def _build_citations(results: list[dict]) -> tuple[list[dict], list[str]]:
    citations: list[dict] = []
    contexts: list[str] = []
    for result in results:
        content = result.get("content", "")
        if content:
            contexts.append(content)
        citations.append(
            {
                "chunk_id": result.get("chunk_id", ""),
                "source_doc_id": result.get("source_doc_id", ""),
                "source_doc_name": result.get("source_doc_name", "unknown"),
                "title_path": result.get("title_path", ""),
                "excerpt": content if content else "",
                "score": result.get("score"),
                "rerank_score": result.get("rerank_score"),
                "bm25_score": result.get("bm25_score"),
                "hybrid_score": result.get("hybrid_score"),
            }
        )
    return citations, contexts


def build_answer_from_results(
    question: str,
    results: list[dict],
    course_name: str | None = None,
    answer_override: str | None = None,
) -> dict[str, Any]:
    citations, contexts = _build_citations(results)

    if answer_override is not None:
        return {"answer": answer_override, "citations": citations, "contexts": contexts}

    if not citations:
        answer = "未找到相关资料，请确认课程知识库已上传。"
        return {"answer": answer, "citations": citations, "contexts": contexts}

    answer = None
    chain = _build_chain()
    if chain:
        answer = chain.invoke(
            {
                "course_name": course_name or "未知课程",
                "question": question,
                "context": _format_context(results),
            }
        )

    if not answer:
        answer = "（占位）基于检索到的资料生成回答，待接入模型后替换。"

    return {"answer": answer, "citations": citations, "contexts": contexts}


def _extract_delta_text(data: Any) -> str:
    try:
        return data.delta.content.text.value
    except Exception:
        try:
            content = getattr(getattr(data, "delta", None), "content", None)
            text_value = getattr(getattr(content, "text", None), "value", "")
            return text_value or ""
        except Exception:
            return ""


def _stream_dashscope_answer(
    question: str,
    context: str,
    course_name: str | None = None,
) -> Iterable[str]:
    assistant = Assistants.create(
        model=os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus").strip() or "qwen-plus",
        name="RAG QA Stream",
        instructions=(
            "你是教学问答助手。仅基于提供的检索内容回答问题，"
            "若材料不足则依据你自己的知识储备回答。"
        ),
    )
    thread = Threads.create(
        assistant_id=assistant.id,
        messages=[
            {
                "role": "user",
                "content": (
                    f"课程：{course_name or '未知课程'}\n"
                    f"问题：{question}\n\n"
                    f"检索资料：\n{context}\n\n回答："
                ),
            }
        ],
    )
    run_iterator = Runs.create(thread.id, assistant_id=assistant.id, stream=True)
    for event, data in run_iterator:
        if event == "thread.message.delta":
            chunk = _extract_delta_text(data)
            if chunk:
                yield chunk


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def stream_answer_events(course_id: str, question: str, top_k: int) -> Iterable[str]:
    course_name = get_course_title(course_id)
    results = search_documents(course_id, question, top_k)
    citations, _contexts = _build_citations(results)

    if not citations:
        answer = "未找到相关资料，请确认课程知识库已上传。"
        yield _format_sse("delta", {"text": answer})
        yield _format_sse("done", {"answer": answer, "citations": citations})
        return

    if not is_dashscope_configured():
        answer = "（占位）基于检索到的资料生成回答，待接入模型后替换。"
        yield _format_sse("delta", {"text": answer})
        yield _format_sse("done", {"answer": answer, "citations": citations})
        return

    context = _format_context(results)
    answer_chunks: list[str] = []
    try:
        for chunk in _stream_dashscope_answer(question, context, course_name=course_name):
            answer_chunks.append(chunk)
            yield _format_sse("delta", {"text": chunk})
    except Exception:
        fallback = "模型响应失败，请稍后重试。"
        if not answer_chunks:
            yield _format_sse("delta", {"text": fallback})
            answer_chunks.append(fallback)
        yield _format_sse("error", {"message": fallback})

    answer = "".join(answer_chunks).strip()
    if not answer:
        answer = "（占位）基于检索到的资料生成回答，待接入模型后替换。"
    yield _format_sse("done", {"answer": answer, "citations": citations})


def answer_question(course_id: str, question: str, top_k: int) -> dict[str, Any]:
    course_name = get_course_title(course_id)
    results = search_documents(course_id, question, top_k)
    payload = build_answer_from_results(question, results, course_name=course_name)
    return {"answer": payload["answer"], "citations": payload["citations"]}
