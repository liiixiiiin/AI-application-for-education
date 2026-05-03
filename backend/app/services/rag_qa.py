import json
import os
from typing import Any, Iterable

from dashscope import Assistants, Generation, Runs, Threads

from .knowledge_base import get_course_title, list_documents, search_documents
from .langchain_client import is_dashscope_configured
from .memory_store import (
    add_message,
    auto_title_from_question,
    get_or_create_conversation,
    get_recent_messages,
)
from .rag_utils import build_answer_from_results, build_citations, format_context


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


def _build_thread_messages(
    question: str,
    context: str,
    course_name: str | None,
    history: list[dict],
) -> list[dict]:
    """Build the DashScope Thread messages list with conversation history."""
    messages: list[dict] = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    user_content = (
        f"课程：{course_name or '未知课程'}\n"
        f"问题：{question}\n\n"
    )
    if context:
        user_content += f"检索资料：\n{context}\n\n"
    user_content += "回答："
    messages.append({"role": "user", "content": user_content})
    return messages


def _stream_generation_answer(
    question: str,
    context: str,
    course_name: str | None = None,
    history: list[dict] | None = None,
    enable_search: bool = False,
) -> Iterable[str | dict]:
    """Stream answer via DashScope Generation API (supports enable_search).

    Yields str chunks for text content. When enable_search is True, also yields
    a dict ``{"web_sources": [...]}`` once when the search results arrive.
    """
    model = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus").strip() or "qwen-plus"
    system_prompt = (
        "你是教学问答助手。基于提供的检索内容回答问题，"
        "若材料不足则依据你自己的知识储备回答。"
        "结合对话历史理解追问与指代关系。"
    )
    if enable_search:
        system_prompt += "你还可以结合联网搜索获取的最新信息来补充回答。"

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in (history or []):
        messages.append({"role": msg["role"], "content": msg["content"]})
    user_content = (
        f"课程：{course_name or '未知课程'}\n"
        f"问题：{question}\n\n"
    )
    if context:
        user_content += f"检索资料：\n{context}\n\n"
    user_content += "回答："
    messages.append({"role": "user", "content": user_content})

    extra_kwargs: dict[str, Any] = {}
    if enable_search:
        extra_kwargs["search_options"] = {
            "forced_search": True,
            "enable_source": True,
            "enable_citation": True,
            "citation_format": "[<number>]",
            "prepend_search_result": True,
        }

    responses = Generation.call(
        model=model,
        messages=messages,
        result_format="message",
        stream=True,
        incremental_output=True,
        enable_search=enable_search,
        **extra_kwargs,
    )
    search_info_emitted = False
    for response in responses:
        if response.status_code == 200:
            if not search_info_emitted and enable_search:
                search_info = response.output.get("search_info")
                if search_info:
                    raw_results = search_info.get("search_results", [])
                    web_sources = [
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "site_name": r.get("site_name", ""),
                            "index": r.get("index"),
                        }
                        for r in raw_results if r.get("url")
                    ]
                    if web_sources:
                        yield {"web_sources": web_sources}
                    search_info_emitted = True
            choices = response.output.get("choices", [])
            if choices:
                delta = choices[0].get("message", {}).get("content", "")
                if delta:
                    yield delta


def _stream_dashscope_answer(
    question: str,
    context: str,
    course_name: str | None = None,
    history: list[dict] | None = None,
    use_web_search: bool = False,
) -> Iterable[str | dict]:
    if use_web_search:
        yield from _stream_generation_answer(
            question, context, course_name=course_name,
            history=history, enable_search=True,
        )
        return

    assistant = Assistants.create(
        model=os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus").strip() or "qwen-plus",
        name="RAG QA Stream",
        instructions=(
            "你是教学问答助手。基于提供的检索内容回答问题，"
            "若材料不足则依据你自己的知识储备回答。"
            "结合对话历史理解追问与指代关系。"
        ),
    )
    thread_messages = _build_thread_messages(question, context, course_name, history or [])
    thread = Threads.create(assistant_id=assistant.id, messages=thread_messages)
    run_iterator = Runs.create(thread.id, assistant_id=assistant.id, stream=True)
    for event, data in run_iterator:
        if event == "thread.message.delta":
            chunk = _extract_delta_text(data)
            if chunk:
                yield chunk


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_answer_events(
    course_id: str,
    question: str,
    top_k: int,
    use_web_search: bool | None = False,
    user_id: str | None = None,
    conversation_id: str | None = None,
) -> Iterable[str]:
    course_name = get_course_title(course_id)
    results = search_documents(course_id, question, top_k)
    citations, _contexts = build_citations(results)
    context = format_context(results)

    conv = None
    history: list[dict] = []
    if user_id:
        conv = get_or_create_conversation(user_id, course_id, conversation_id)
        history = get_recent_messages(conv["id"])
        add_message(conv["id"], "user", question)
        auto_title_from_question(conv["id"], question)

    resolved_conv_id = conv["id"] if conv else None

    disclaimer = ""
    if not citations:
        docs = list_documents(course_id)
        if not docs:
            disclaimer = "**注意：** 该课程尚未上传知识库资料，以下回答基于模型自身知识，仅供参考。\n\n"
        else:
            disclaimer = "**注意：** 未在课程知识库中检索到直接相关的资料，以下回答基于模型自身知识，仅供参考。\n\n"

    if not is_dashscope_configured():
        answer = disclaimer + "（占位）模型服务未配置，待接入后可生成回答。"
        if conv:
            add_message(conv["id"], "assistant", answer, [])
        yield _format_sse("delta", {"text": answer})
        yield _format_sse("done", {"answer": answer, "citations": citations, "conversation_id": resolved_conv_id})
        return

    answer_chunks: list[str] = []
    web_sources: list[dict] = []
    has_llm_content = False

    if disclaimer:
        yield _format_sse("delta", {"text": disclaimer})
        answer_chunks.append(disclaimer)

    try:
        for chunk in _stream_dashscope_answer(
            question, context, course_name=course_name, history=history, use_web_search=bool(use_web_search),
        ):
            if isinstance(chunk, dict):
                web_sources = chunk.get("web_sources", [])
                yield _format_sse("web_sources", {"sources": web_sources})
            else:
                has_llm_content = True
                answer_chunks.append(chunk)
                yield _format_sse("delta", {"text": chunk})
    except Exception:
        fallback = "模型响应失败，请稍后重试。"
        if not has_llm_content:
            yield _format_sse("delta", {"text": fallback})
            answer_chunks.append(fallback)
        yield _format_sse("error", {"message": fallback})

    answer = "".join(answer_chunks).strip()
    if not answer:
        answer = "（占位）基于检索到的资料生成回答，待接入模型后替换。"

    if conv:
        citations_for_db = [c for c in citations]
        add_message(conv["id"], "assistant", answer, citations_for_db)

    done_payload: dict[str, Any] = {
        "answer": answer,
        "citations": citations,
        "conversation_id": resolved_conv_id,
    }
    if web_sources:
        done_payload["web_sources"] = web_sources
    if disclaimer:
        done_payload["disclaimer"] = disclaimer.strip()
    yield _format_sse("done", done_payload)


def answer_question(
    course_id: str,
    question: str,
    top_k: int,
    use_web_search: bool | None = False,
    user_id: str | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    course_name = get_course_title(course_id)
    results = search_documents(course_id, question, top_k)

    disclaimer = ""
    if not results:
        docs = list_documents(course_id)
        if not docs:
            disclaimer = "**注意：** 该课程尚未上传知识库资料，以下回答基于模型自身知识，仅供参考。\n\n"
        else:
            disclaimer = "**注意：** 未在课程知识库中检索到直接相关的资料，以下回答基于模型自身知识，仅供参考。\n\n"

    conv = None
    history: list[dict] = []
    if user_id:
        conv = get_or_create_conversation(user_id, course_id, conversation_id)
        history = get_recent_messages(conv["id"])
        add_message(conv["id"], "user", question)
        auto_title_from_question(conv["id"], question)

    payload = build_answer_from_results(
        question, results, course_name=course_name, history=history, disclaimer=disclaimer,
    )

    if conv:
        add_message(conv["id"], "assistant", payload["answer"], payload.get("citations", []))

    result: dict[str, Any] = {
        "answer": payload["answer"],
        "citations": payload["citations"],
        "conversation_id": conv["id"] if conv else None,
    }
    if disclaimer:
        result["disclaimer"] = disclaimer.strip()
    return result
