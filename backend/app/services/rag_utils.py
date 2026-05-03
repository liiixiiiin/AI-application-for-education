import json
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .langchain_client import get_chat_model, is_dashscope_configured


def format_context(results: list[dict]) -> str:
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


def _format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = []
    for msg in history:
        role_label = "用户" if msg["role"] == "user" else "助手"
        lines.append(f"{role_label}：{msg['content']}")
    return "\n".join(lines)


def build_chain(with_history: bool = False):
    if not is_dashscope_configured():
        return None
    llm = get_chat_model()
    if not llm:
        return None
    if with_history:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是教学问答助手。仅基于提供的检索内容回答问题，"
                    "若材料不足则依据你自己的知识储备回答。"
                    "结合对话历史理解追问与指代关系。",
                ),
                (
                    "user",
                    "课程：{course_name}\n\n对话历史：\n{history}\n\n"
                    "当前问题：{question}\n\n检索资料：\n{context}\n\n回答：",
                ),
            ]
        )
    else:
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


def build_mcp_router_chain():
    if not is_dashscope_configured():
        return None
    llm = get_chat_model()
    if not llm:
        return None
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是工具路由助手。根据用户意图在工具列表中选择最合适的工具，"
                "并给出工具调用参数。仅输出 JSON，格式示例："
                '{{"tool": "<tool_name>", "args": {{"key": "value"}}}}。',
            ),
            (
                "user",
                "用户意图：{instruction}\n\n工具列表：\n{tool_list}\n\n请输出 JSON：",
            ),
        ]
    )
    return prompt | llm | StrOutputParser()


def _tool_list_text(tools: list[Any]) -> str:
    lines = []
    for tool in tools:
        name = getattr(tool, "name", "unknown")
        desc = getattr(tool, "description", "")
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def _select_mcp_tool(
    tools: list[Any],
    instruction: str,
) -> tuple[Any | None, dict]:
    if not tools:
        return None, {}
    chain = build_mcp_router_chain()
    if not chain:
        return None, {}
    raw = chain.invoke({"instruction": instruction, "tool_list": _tool_list_text(tools)})
    if not raw:
        return None, {}
    try:
        payload = json.loads(str(raw))
    except json.JSONDecodeError:
        return None, {}
    tool_name = str(payload.get("tool", "")).strip()
    args = payload.get("args") if isinstance(payload.get("args"), dict) else {}
    selected = next((tool for tool in tools if getattr(tool, "name", "") == tool_name), None)
    return selected, args


def build_citations(results: list[dict]) -> tuple[list[dict], list[str]]:
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
    history: list[dict] | None = None,
    disclaimer: str = "",
) -> dict[str, Any]:
    citations, contexts = build_citations(results)

    if answer_override is not None:
        answer = disclaimer + answer_override if disclaimer else answer_override
        return {"answer": answer, "citations": citations, "contexts": contexts}

    answer = None
    has_history = bool(history)
    chain = build_chain(with_history=has_history)
    if chain:
        invoke_args: dict[str, str] = {
            "course_name": course_name or "未知课程",
            "question": question,
            "context": format_context(results),
        }
        if has_history:
            invoke_args["history"] = _format_history(history)  # type: ignore[arg-type]
        answer = chain.invoke(invoke_args)

    if not answer:
        answer = "（占位）基于检索到的资料生成回答，待接入模型后替换。"

    full_answer = disclaimer + answer if disclaimer else answer
    return {"answer": full_answer, "citations": citations, "contexts": contexts}
