"""反思纠错节点（agent-spec §3.4 / §5）。

校验维度：
- json_schema：每个工具结果包含 output_required_fields
- format_check（exercise_gen）：每题完整字段
- kp_match（exercise_gen / lesson_plan）：知识点不在指定范围则失败
- coverage（lesson_plan）：提纲必须覆盖请求中的所有 knowledge_points
- time_budget：累计耗时 > 阈值 → 直接进入 aggregator（强制通过）

反思失败 ≤1 次时返回 planner 重做；超过则强制聚合并打 degraded。
"""

from __future__ import annotations

import logging
from typing import Any

from ..intents import Intent
from ..state import AgentState, ReflectVerdict, time_exhausted
from ..tools import REGISTRY

logger = logging.getLogger(__name__)

MAX_PLAN_REPLAN = 1


def _check_json_schema(state: AgentState) -> tuple[bool, list[str]]:
    failed: list[str] = []
    for step in state.get("step_results") or []:
        if not step.get("success"):
            failed.append(f"{step.get('tool_name')}:exception")
            continue
        spec = REGISTRY.get(step.get("tool_name") or "")
        if not spec:
            continue
        result = step.get("result")
        if not isinstance(result, dict):
            failed.append(f"{step.get('tool_name')}:not_dict")
            continue
        for field in spec.output_required_fields:
            if field not in result:
                failed.append(f"{step.get('tool_name')}:missing_{field}")
    return (not failed, failed)


def _check_exercise_format(state: AgentState) -> tuple[bool, list[str]]:
    failed: list[str] = []
    for step in state.get("step_results") or []:
        if step.get("tool_name") != "generate_exercise" or not step.get("success"):
            continue
        items = (step.get("result") or {}).get("generated") or []
        for ex in items:
            if not isinstance(ex, dict):
                continue
            etype = ex.get("type")
            if not ex.get("question"):
                failed.append(f"{ex.get('exercise_id')}:missing_question")
            if etype == "single_choice":
                if not ex.get("options") or not ex.get("answer"):
                    failed.append(f"{ex.get('exercise_id')}:missing_options_or_answer")
            if etype == "fill_in_blank" and not ex.get("blanks"):
                failed.append(f"{ex.get('exercise_id')}:missing_blanks")
            if etype == "short_answer" and not ex.get("rubric"):
                failed.append(f"{ex.get('exercise_id')}:missing_rubric")
    return (not failed, failed)


def _check_kp_match(state: AgentState) -> tuple[bool, list[str]]:
    intent = state.get("intent")
    if intent not in {Intent.EXERCISE_GEN.value, Intent.LESSON_PLAN.value, Intent.RECOMMEND.value}:
        return True, []
    requested: set[str] = set()
    for step in state.get("plan") or []:
        for key in ("knowledge_scope", "knowledge_points"):
            scope = (step.get("tool_args") or {}).get(key)
            if isinstance(scope, list):
                requested.update(str(s) for s in scope if s)
    if not requested:
        return True, []
    failed: list[str] = []
    for step in state.get("step_results") or []:
        if step.get("tool_name") != "generate_exercise" or not step.get("success"):
            continue
        for ex in (step.get("result") or {}).get("generated") or []:
            kps = set(str(k) for k in (ex.get("knowledge_points") or []))
            if kps and not kps & requested:
                failed.append(f"{ex.get('exercise_id')}:kp_not_in_scope")
    return (not failed, failed)


def _check_coverage(state: AgentState) -> tuple[bool, list[str]]:
    if state.get("intent") != Intent.LESSON_PLAN.value:
        return True, []
    expected_kps: set[str] = set()
    for step in state.get("plan") or []:
        if step.get("tool_name") == "lesson_outline":
            kps = (step.get("tool_args") or {}).get("knowledge_points")
            if isinstance(kps, list):
                expected_kps.update(str(k) for k in kps if k)
    if not expected_kps:
        return True, []
    outline_step = next(
        (
            s
            for s in (state.get("step_results") or [])
            if s.get("tool_name") == "lesson_outline" and s.get("success")
        ),
        None,
    )
    if not outline_step:
        return True, []
    outline = outline_step.get("result") or {}
    covered: set[str] = set()
    for field in ("key_points", "objectives", "difficult_points"):
        for item in outline.get(field) or []:
            text = str(item)
            for kp in expected_kps:
                if kp in text:
                    covered.add(kp)
    missing = expected_kps - covered
    if missing:
        return False, [f"missing_kp:{kp}" for kp in missing]
    return True, []


def _check_grade_consistency(state: AgentState) -> tuple[bool, list[str]]:
    if state.get("intent") != Intent.EXERCISE_GRADE.value:
        return True, []
    failed: list[str] = []
    for step in state.get("step_results") or []:
        if step.get("tool_name") != "grade_answer" or not step.get("success"):
            continue
        result: Any = step.get("result") or {}
        if not isinstance(result, dict):
            failed.append("grade:not_dict")
            continue
        score = result.get("score")
        if not isinstance(score, (int, float)) or not (0 <= score <= 1):
            failed.append("grade:bad_score")
    return (not failed, failed)


def reflector_node(state: AgentState) -> dict:
    if time_exhausted(state):
        verdict: ReflectVerdict = {
            "pass_": True,
            "reason": "time_budget_exceeded:force_aggregate",
            "failed_dimensions": ["time_budget"],
            "suggestion": "",
        }
        history = list(state.get("reflect_history") or []) + [verdict]
        logger.warning("reflector forced pass due to time budget")
        return {"reflect_history": history, "degraded": True}

    plan_complete = int(state.get("cursor") or 0) >= len(state.get("plan") or [])
    if not plan_complete:
        return {}

    schema_ok, schema_fail = _check_json_schema(state)
    fmt_ok, fmt_fail = _check_exercise_format(state)
    kp_ok, kp_fail = _check_kp_match(state)
    cov_ok, cov_fail = _check_coverage(state)
    grade_ok, grade_fail = _check_grade_consistency(state)

    failed_dims: list[str] = []
    if not schema_ok:
        failed_dims.append("json_schema")
    if not fmt_ok:
        failed_dims.append("format_check")
    if not kp_ok:
        failed_dims.append("kp_match")
    if not cov_ok:
        failed_dims.append("coverage")
    if not grade_ok:
        failed_dims.append("grade_consistency")

    passed = not failed_dims
    suggestion = ""
    if not passed:
        suggestion = (
            "失败维度："
            + ",".join(failed_dims)
            + "；详情："
            + "; ".join(schema_fail + fmt_fail + kp_fail + cov_fail + grade_fail)[:280]
        )

    history = list(state.get("reflect_history") or [])
    plan_attempts = int(state.get("plan_attempts") or 0)
    forced_degrade = False
    if not passed and plan_attempts > MAX_PLAN_REPLAN:
        passed = True
        forced_degrade = True
        suggestion += " | 已达 replan 上限，强制通过"

    history.append(
        ReflectVerdict(
            pass_=passed,
            reason="ok" if passed and not forced_degrade else "validation_failed",
            failed_dimensions=failed_dims,
            suggestion=suggestion,
        )
    )

    update: dict = {"reflect_history": history}
    if forced_degrade:
        update["degraded"] = True
    logger.info(
        "reflector: pass=%s failed=%s degrade=%s", passed, failed_dims, forced_degrade
    )
    return update
