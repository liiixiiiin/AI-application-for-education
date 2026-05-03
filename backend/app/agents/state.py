"""Agent 状态机数据结构（agent-spec §2-3）。"""

from __future__ import annotations

import time
from typing import Any, TypedDict

from .intents import Intent


class PlannedStep(TypedDict, total=False):
    """单步执行计划。"""

    step_id: str
    tool_name: str
    tool_args: dict[str, Any]
    description: str  # 该步骤目的的简短说明（可选，便于流式展示与调试）


class StepResult(TypedDict, total=False):
    """单步工具调用结果。"""

    step_id: str
    tool_name: str
    tool_args: dict[str, Any]
    success: bool
    result: Any
    result_summary: str
    error: str | None
    retries: int
    duration_ms: int


class ReflectVerdict(TypedDict, total=False):
    """反思节点输出。"""

    pass_: bool
    reason: str
    failed_dimensions: list[str]
    suggestion: str  # 给 planner 的修复建议（自然语言）


class AgentState(TypedDict, total=False):
    """LangGraph 共享状态。

    所有节点读写均通过此 dict；LangGraph 框架按节点返回值合并。
    """

    # ── 输入 ──
    user_input: str
    course_id: str | None
    user_id: str | None
    student_id: str | None
    conversation_id: str | None
    extra_inputs: dict[str, Any]  # 透传（如 exercise_id / answer 等）

    # ── 配置 ──
    run_id: str
    started_at: float  # time.time()
    time_budget_seconds: float

    # ── 中间结果 ──
    intent: str
    skill: str | None
    plan: list[PlannedStep]
    cursor: int  # 下一个待执行 step 的下标
    step_results: list[StepResult]
    reflect_history: list[ReflectVerdict]
    plan_attempts: int  # planner 重试计数（上限 1）

    # ── 输出 ──
    answer: dict[str, Any] | str
    degraded: bool
    error: str | None


def new_state(
    *,
    user_input: str,
    course_id: str | None = None,
    user_id: str | None = None,
    conversation_id: str | None = None,
    extra_inputs: dict[str, Any] | None = None,
    run_id: str = "",
    time_budget_seconds: float = 60.0,
) -> AgentState:
    return AgentState(
        user_input=user_input,
        course_id=course_id,
        user_id=user_id,
        student_id=user_id,
        conversation_id=conversation_id,
        extra_inputs=extra_inputs or {},
        run_id=run_id,
        started_at=time.time(),
        time_budget_seconds=time_budget_seconds,
        intent=Intent.UNKNOWN.value,
        skill=None,
        plan=[],
        cursor=0,
        step_results=[],
        reflect_history=[],
        plan_attempts=0,
        answer="",
        degraded=False,
        error=None,
    )


def time_elapsed(state: AgentState) -> float:
    started = state.get("started_at") or time.time()
    return max(0.0, time.time() - started)


def time_exhausted(state: AgentState) -> bool:
    budget = float(state.get("time_budget_seconds") or 60.0)
    return time_elapsed(state) >= budget
