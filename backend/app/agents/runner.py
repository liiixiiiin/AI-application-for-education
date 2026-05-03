"""Agent 对外入口（agent-spec §9）。

提供两种调用方式：
- run_agent(...)：同步阻塞返回最终结构化结果（用于评测脚本与非流式 API）
- stream_agent_events(...)：返回 SSE 事件迭代器（intent / plan / tool_start / tool_end / reflect / done）
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Iterable

from ..utils import generate_id
from .graph import get_agent_graph
from .state import AgentState, new_state

logger = logging.getLogger(__name__)


# ── 工具：把 state 关键信息序列化为 JSON 友好结构 ──


def _serialize_step_for_event(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": step.get("step_id"),
        "tool": step.get("tool_name"),
        "args": step.get("tool_args"),
        "success": step.get("success"),
        "summary": step.get("result_summary"),
        "duration_ms": step.get("duration_ms"),
        "retries": step.get("retries"),
        "error": step.get("error"),
    }


def _format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# ── 同步入口 ──────────────────────────────────────────────────────────


def run_agent(
    *,
    user_input: str,
    course_id: str | None = None,
    user_id: str | None = None,
    conversation_id: str | None = None,
    extra_inputs: dict[str, Any] | None = None,
    time_budget_seconds: float = 60.0,
    run_id: str | None = None,
) -> dict[str, Any]:
    """运行一次 Agent，返回结构化最终响应。"""

    graph = get_agent_graph()
    rid = run_id or generate_id("run")
    started = time.time()

    initial: AgentState = new_state(
        user_input=user_input,
        course_id=course_id,
        user_id=user_id,
        conversation_id=conversation_id,
        extra_inputs=extra_inputs,
        run_id=rid,
        time_budget_seconds=time_budget_seconds,
    )

    try:
        final_state: AgentState = graph.invoke(initial)
    except Exception as exc:
        logger.exception("Agent run failed: %s", exc)
        return {
            "run_id": rid,
            "intent": initial.get("intent"),
            "skill": None,
            "answer": {
                "type": "error",
                "answer": f"Agent 执行异常：{exc}",
            },
            "steps": [],
            "reflect_history": [],
            "degraded": True,
            "error": str(exc),
            "duration_ms": int((time.time() - started) * 1000),
        }

    answer = final_state.get("answer") or {}
    if not isinstance(answer, dict):
        answer = {"answer": str(answer)}

    return {
        "run_id": rid,
        "intent": final_state.get("intent"),
        "skill": final_state.get("skill"),
        "answer": answer,
        "steps": [
            _serialize_step_for_event(step) for step in final_state.get("step_results") or []
        ],
        "reflect_history": final_state.get("reflect_history") or [],
        "degraded": bool(final_state.get("degraded")),
        "duration_ms": int((time.time() - started) * 1000),
    }


# ── 流式入口（SSE）─────────────────────────────────────────────────────


def stream_agent_events(
    *,
    user_input: str,
    course_id: str | None = None,
    user_id: str | None = None,
    conversation_id: str | None = None,
    extra_inputs: dict[str, Any] | None = None,
    time_budget_seconds: float = 60.0,
    run_id: str | None = None,
) -> Iterable[str]:
    """以 SSE 事件流形式返回 Agent 执行过程。

    事件序列：
    - run_start：包含 run_id
    - intent：意图识别完成
    - plan：planner 输出步骤列表
    - tool_start / tool_end：每步工具调用
    - reflect：反思结果
    - done：最终聚合输出
    """

    graph = get_agent_graph()
    rid = run_id or generate_id("run")
    started = time.time()

    initial: AgentState = new_state(
        user_input=user_input,
        course_id=course_id,
        user_id=user_id,
        conversation_id=conversation_id,
        extra_inputs=extra_inputs,
        run_id=rid,
        time_budget_seconds=time_budget_seconds,
    )

    yield _format_sse("run_start", {"run_id": rid})

    last_step_count = 0
    last_intent_emitted = False
    last_plan_emitted = False
    last_reflect_count = 0
    final_state: AgentState | None = None

    try:
        for event in graph.stream(initial, stream_mode="values"):
            current: AgentState = event  # stream_mode=values 时 event 即为最新 state
            final_state = current

            if not last_intent_emitted and current.get("intent") and current.get("intent") != "unknown":
                yield _format_sse(
                    "intent",
                    {
                        "intent": current.get("intent"),
                        "skill": current.get("skill"),
                    },
                )
                last_intent_emitted = True

            plan = current.get("plan") or []
            if not last_plan_emitted and plan:
                yield _format_sse(
                    "plan",
                    {
                        "steps": [
                            {
                                "step_id": p.get("step_id"),
                                "tool": p.get("tool_name"),
                                "args": p.get("tool_args"),
                                "description": p.get("description"),
                            }
                            for p in plan
                        ],
                    },
                )
                last_plan_emitted = True

            steps = current.get("step_results") or []
            while last_step_count < len(steps):
                step = steps[last_step_count]
                yield _format_sse("tool_start", {
                    "step_id": step.get("step_id"),
                    "tool": step.get("tool_name"),
                    "args": step.get("tool_args"),
                })
                yield _format_sse("tool_end", _serialize_step_for_event(step))
                last_step_count += 1

            reflects = current.get("reflect_history") or []
            while last_reflect_count < len(reflects):
                v = reflects[last_reflect_count]
                yield _format_sse(
                    "reflect",
                    {
                        "pass": bool(v.get("pass_")),
                        "failed_dimensions": v.get("failed_dimensions") or [],
                        "suggestion": v.get("suggestion") or "",
                        "reason": v.get("reason") or "",
                    },
                )
                last_reflect_count += 1
    except Exception as exc:
        logger.exception("Agent stream failed: %s", exc)
        yield _format_sse(
            "done",
            {
                "run_id": rid,
                "answer": {"type": "error", "answer": f"Agent 执行异常：{exc}"},
                "error": str(exc),
                "degraded": True,
                "duration_ms": int((time.time() - started) * 1000),
            },
        )
        return

    answer = (final_state or {}).get("answer") or {}
    if not isinstance(answer, dict):
        answer = {"answer": str(answer)}

    yield _format_sse(
        "done",
        {
            "run_id": rid,
            "intent": (final_state or {}).get("intent"),
            "skill": (final_state or {}).get("skill"),
            "answer": answer,
            "degraded": bool((final_state or {}).get("degraded")),
            "duration_ms": int((time.time() - started) * 1000),
        },
    )
