"""结果聚合节点（agent-spec §3.5）。

按意图把工具结果合成最终响应；qa 意图额外用 LLM 做一次综述。
"""

from __future__ import annotations

import logging
from typing import Any

from ...services.memory_store import add_message, get_or_create_conversation
from ...services.rag_utils import build_citations
from ..intents import Intent
from ..llm import call_text, llm_available, safe_json_dumps
from ..state import AgentState

logger = logging.getLogger(__name__)


def _last_step(state: AgentState, tool_name: str) -> dict | None:
    for step in reversed(state.get("step_results") or []):
        if step.get("tool_name") == tool_name and step.get("success"):
            return step
    return None


def _aggregate_qa(state: AgentState) -> dict[str, Any]:
    user_input = state.get("user_input", "")
    course_id = state.get("course_id") or ""
    search_step = _last_step(state, "search_kb")
    web_step = _last_step(state, "web_search")

    citations: list[dict[str, Any]] = []
    contexts: list[str] = []
    if search_step:
        results = (search_step.get("result") or {}).get("results") or []
        citations, contexts = build_citations(results)

    if web_step:
        # web_search 已经返回完整 answer，直接用
        web_payload = web_step.get("result") or {}
        return {
            "type": Intent.QA.value,
            "answer": web_payload.get("answer") or "（联网搜索无结果）",
            "citations": web_payload.get("citations") or citations,
            "disclaimer": web_payload.get("disclaimer"),
        }

    answer_text: str | None = None
    if llm_available() and contexts:
        context_block = "\n\n".join(
            f"[{idx}] {ctx[:600]}" for idx, ctx in enumerate(contexts, start=1)
        )
        system_prompt = (
            "你是教学问答助手。基于提供的检索片段回答问题，"
            "若材料不足则结合常识简洁补充，并标注【依据不足】。"
        )
        user_prompt = (
            f"课程ID：{course_id}\n问题：{user_input}\n\n检索片段：\n{context_block}\n\n回答："
        )
        answer_text = call_text(system_prompt, user_prompt)

    if not answer_text:
        if contexts:
            answer_text = "\n".join(contexts[:3])[:1200]
        else:
            answer_text = "（未在课程知识库中找到相关资料，建议检查课程是否上传了知识点文档。）"

    return {
        "type": Intent.QA.value,
        "answer": answer_text,
        "citations": citations,
    }


def _aggregate_exercise_gen(state: AgentState) -> dict[str, Any]:
    step = _last_step(state, "generate_exercise")
    if not step:
        return {"type": Intent.EXERCISE_GEN.value, "generated": [], "answer": "未生成任何题目。"}
    generated = (step.get("result") or {}).get("generated") or []
    return {
        "type": Intent.EXERCISE_GEN.value,
        "generated": generated,
        "answer": f"已生成 {len(generated)} 道练习。",
    }


def _aggregate_exercise_grade(state: AgentState) -> dict[str, Any]:
    step = _last_step(state, "grade_answer")
    if not step:
        return {"type": Intent.EXERCISE_GRADE.value, "answer": "评分失败。"}
    grading = step.get("result") or {}
    return {
        "type": Intent.EXERCISE_GRADE.value,
        "grading": grading,
        "answer": grading.get("feedback") or "评分完成。",
    }


def _aggregate_lesson_plan(state: AgentState) -> dict[str, Any]:
    outline_step = _last_step(state, "lesson_outline")
    exercise_step = _last_step(state, "generate_exercise")
    outline = outline_step.get("result") if outline_step else None
    generated = (exercise_step.get("result") or {}).get("generated") if exercise_step else []
    return {
        "type": Intent.LESSON_PLAN.value,
        "outline": outline,
        "exercises": generated or [],
        "answer": (
            f"备课完成：提纲已生成（{len(outline.get('teaching_flow') or []) if outline else 0} 模块），"
            f"配套练习 {len(generated or [])} 道。"
        ),
    }


def _aggregate_recommend(state: AgentState) -> dict[str, Any]:
    mastery_step = _last_step(state, "get_mastery")
    exercise_step = _last_step(state, "generate_exercise")
    mastery = mastery_step.get("result") if mastery_step else None
    weak = (mastery or {}).get("weak_points") or []
    generated = (exercise_step.get("result") or {}).get("generated") if exercise_step else []
    return {
        "type": Intent.RECOMMEND.value,
        "weak_points": weak,
        "mastery_overview": (mastery or {}).get("items") or [],
        "exercises": generated or [],
        "answer": (
            f"识别到 {len(weak)} 个薄弱知识点，已生成 {len(generated or [])} 道针对性练习。"
        ),
    }


def _aggregate_mixed(state: AgentState) -> dict[str, Any]:
    """通用聚合：把每步结果摘要拼接为文本回答。"""

    lines: list[str] = []
    payload: dict[str, Any] = {"type": Intent.MIXED.value, "steps": []}
    for step in state.get("step_results") or []:
        payload["steps"].append(
            {
                "tool": step.get("tool_name"),
                "success": step.get("success"),
                "summary": step.get("result_summary"),
            }
        )
        lines.append(f"- {step.get('tool_name')}: {step.get('result_summary')}")
    payload["answer"] = "执行结果：\n" + "\n".join(lines) if lines else "未执行任何步骤。"
    return payload


_AGGREGATORS = {
    Intent.QA.value: _aggregate_qa,
    Intent.EXERCISE_GEN.value: _aggregate_exercise_gen,
    Intent.EXERCISE_GRADE.value: _aggregate_exercise_grade,
    Intent.LESSON_PLAN.value: _aggregate_lesson_plan,
    Intent.RECOMMEND.value: _aggregate_recommend,
    Intent.MIXED.value: _aggregate_mixed,
}


def _persist_to_memory(state: AgentState, answer_obj: dict[str, Any]) -> None:
    """对 qa 意图持久化到 messages 表，复用现有对话记忆体系。"""

    if state.get("intent") != Intent.QA.value:
        return
    user_id = state.get("user_id")
    course_id = state.get("course_id")
    if not user_id or not course_id:
        return
    try:
        conv = get_or_create_conversation(
            user_id, course_id, state.get("conversation_id")
        )
        add_message(conv["id"], "user", state.get("user_input", ""))
        add_message(
            conv["id"],
            "assistant",
            str(answer_obj.get("answer") or ""),
            answer_obj.get("citations") or [],
        )
    except Exception:
        logger.exception("Failed to persist agent qa answer to memory")


def aggregator_node(state: AgentState) -> dict:
    intent = state.get("intent") or Intent.QA.value
    builder = _AGGREGATORS.get(intent, _aggregate_mixed)
    answer_obj = builder(state)

    answer_obj["intent"] = intent
    answer_obj["skill"] = state.get("skill")
    answer_obj["degraded"] = bool(state.get("degraded"))
    answer_obj["steps"] = [
        {
            "tool": step.get("tool_name"),
            "args": step.get("tool_args"),
            "success": step.get("success"),
            "summary": step.get("result_summary"),
            "duration_ms": step.get("duration_ms"),
            "retries": step.get("retries"),
            "error": step.get("error"),
        }
        for step in (state.get("step_results") or [])
    ]
    answer_obj["reflect_history"] = state.get("reflect_history") or []

    _persist_to_memory(state, answer_obj)

    logger.info(
        "aggregator: intent=%s steps=%s degraded=%s",
        intent,
        len(answer_obj.get("steps", [])),
        answer_obj["degraded"],
    )
    return {"answer": answer_obj}
