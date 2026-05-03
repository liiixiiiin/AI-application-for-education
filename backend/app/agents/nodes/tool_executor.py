"""工具调用节点（agent-spec §3.3）。

执行 plan[cursor] 一步，写入 step_results，cursor += 1。
- 单步重试上限：2 次（含首次共 3 次尝试）
- 单步超时：>15s 视为软超时（仅记录），DashScope 客户端层自带网络超时
- 步骤间依赖：自动从前一步结果回填关键字段（如 search_kb → 后续 knowledge_scope）
"""

from __future__ import annotations

import logging
import time
from typing import Any

from ..state import AgentState, PlannedStep, StepResult
from ..tools import REGISTRY, get_tool, summarize_result

logger = logging.getLogger(__name__)

MAX_STEP_RETRIES = 2
SOFT_TIMEOUT_MS = 15_000


# ── 步骤间依赖回填 ────────────────────────────────────────────────────


def _backfill_args(state: AgentState, step: PlannedStep) -> PlannedStep:
    """根据已有 step_results 把空字段回填。

    目前实现：
    - generate_exercise.knowledge_scope 为空时，使用前置 get_mastery 的 weak_points
    - lesson_outline / generate_exercise / search_kb 的 course_id 为空时，回填 state.course_id
    - get_mastery / grade_answer 的 student_id / course_id 同上
    """

    args = dict(step.get("tool_args") or {})
    tool_name = step.get("tool_name")

    course_id = state.get("course_id") or ""
    student_id = state.get("student_id") or state.get("user_id") or ""

    if "course_id" in args and not args.get("course_id"):
        args["course_id"] = course_id
    if "student_id" in args and not args.get("student_id"):
        args["student_id"] = student_id

    if tool_name == "generate_exercise" and not args.get("knowledge_scope"):
        for prev in reversed(state.get("step_results") or []):
            if prev.get("tool_name") == "get_mastery" and prev.get("success"):
                weak = (prev.get("result") or {}).get("weak_points") or []
                if weak:
                    args["knowledge_scope"] = weak[:8]
                    break
                items = (prev.get("result") or {}).get("items") or []
                items_sorted = sorted(items, key=lambda x: x.get("mastery", 1.0))
                if items_sorted:
                    args["knowledge_scope"] = [
                        item["knowledge_point"] for item in items_sorted[:5]
                    ]
                    break

    if tool_name in {"search_kb", "web_search"} and not args.get("query"):
        args["query"] = state.get("user_input", "")

    step["tool_args"] = args
    return step


# ── 节点入口 ──────────────────────────────────────────────────────────


def tool_executor_node(state: AgentState) -> dict:
    plan = list(state.get("plan") or [])
    cursor = int(state.get("cursor") or 0)
    if cursor >= len(plan):
        return {}

    step = _backfill_args(state, dict(plan[cursor]))
    plan[cursor] = step
    tool_name = step.get("tool_name") or ""
    tool = get_tool(tool_name)

    started = time.time()
    retries = 0
    success = False
    result: Any = None
    error: str | None = None
    summary = ""

    if not tool:
        error = f"未注册的工具：{tool_name}"
        summary = error
    else:
        last_exc: Exception | None = None
        while retries <= MAX_STEP_RETRIES:
            try:
                result = tool.call(step.get("tool_args") or {})
                success = True
                summary = summarize_result(tool_name, result)
                break
            except Exception as exc:  # noqa: BLE001 — 工具异常向上聚合
                last_exc = exc
                retries += 1
                logger.warning(
                    "tool %s failed (attempt=%s): %s", tool_name, retries, exc
                )
        if not success and last_exc is not None:
            error = f"{type(last_exc).__name__}: {last_exc}"
            summary = error[:120]

    duration_ms = int((time.time() - started) * 1000)
    if duration_ms > SOFT_TIMEOUT_MS:
        logger.warning(
            "tool %s soft timeout: %sms (>%sms)", tool_name, duration_ms, SOFT_TIMEOUT_MS
        )

    step_result: StepResult = {
        "step_id": step.get("step_id", ""),
        "tool_name": tool_name,
        "tool_args": step.get("tool_args") or {},
        "success": success,
        "result": result,
        "result_summary": summary,
        "error": error,
        "retries": max(0, retries - (0 if success else 1)) if success else retries,
        "duration_ms": duration_ms,
    }

    new_results = list(state.get("step_results") or [])
    new_results.append(step_result)

    return {
        "plan": plan,
        "cursor": cursor + 1,
        "step_results": new_results,
    }
