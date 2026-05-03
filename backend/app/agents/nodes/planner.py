"""任务拆解节点（agent-spec §3.2）。

简单意图直接套用 Skill 预设步骤序列；mixed 意图调用 LLM 自由拆解。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ...utils import generate_id
from ..intents import Intent
from ..llm import call_json, llm_available
from ..state import AgentState, PlannedStep
from ..tools import REGISTRY

logger = logging.getLogger(__name__)


# ── 通用工具 ──────────────────────────────────────────────────────────


def _step(tool: str, args: dict[str, Any], description: str = "") -> PlannedStep:
    return PlannedStep(
        step_id=generate_id("step"),
        tool_name=tool,
        tool_args=args,
        description=description,
    )


def _extract_int(text: str, default: int) -> int:
    match = re.search(r"(\d+)", text)
    if not match:
        return default
    try:
        value = int(match.group(1))
        return max(1, min(20, value))
    except ValueError:
        return default


def _extract_chapter_title(user_input: str) -> str:
    cleaned = user_input.strip()
    cleaned = re.sub(r"(请|帮我|帮忙|麻烦)", "", cleaned)
    for keyword in ["备课", "准备", "出一章", "出题", "推荐", "评分", "判一下"]:
        cleaned = cleaned.replace(keyword, "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip("，。, .")
    return cleaned or user_input.strip()


def _extract_types(user_input: str) -> list[str]:
    text = user_input.lower()
    selected: list[str] = []
    if "单选" in user_input or "选择题" in user_input:
        selected.append("single_choice")
    if "判断" in user_input:
        selected.append("true_false")
    if "填空" in user_input:
        selected.append("fill_in_blank")
    if "简答" in user_input or "问答题" in user_input:
        selected.append("short_answer")
    return selected or ["single_choice"]


def _extract_difficulty(user_input: str) -> str:
    if any(kw in user_input for kw in ["简单", "基础", "入门", "easy"]):
        return "easy"
    if any(kw in user_input for kw in ["难", "进阶", "高难", "hard"]):
        return "hard"
    if any(kw in user_input for kw in ["中等", "medium"]):
        return "medium"
    return "easy"


# ── Skill / Intent 预设 ───────────────────────────────────────────────


def _plan_qa(state: AgentState) -> list[PlannedStep]:
    user_input = state.get("user_input", "")
    course_id = state.get("course_id") or ""
    return [
        _step(
            "search_kb",
            {"course_id": course_id, "query": user_input, "top_k": 5},
            description="检索课程知识库",
        )
    ]


def _plan_exercise_gen(state: AgentState) -> list[PlannedStep]:
    user_input = state.get("user_input", "")
    course_id = state.get("course_id") or ""
    extra = state.get("extra_inputs") or {}
    count = int(extra.get("count") or _extract_int(user_input, 5))
    types = list(extra.get("types") or _extract_types(user_input))
    difficulty = str(extra.get("difficulty") or _extract_difficulty(user_input))
    knowledge_scope = extra.get("knowledge_scope")
    return [
        _step(
            "generate_exercise",
            {
                "course_id": course_id,
                "count": count,
                "types": types,
                "difficulty": difficulty,
                "knowledge_scope": knowledge_scope,
            },
            description=f"生成 {count} 道{('/'.join(types))}",
        )
    ]


def _plan_exercise_grade(state: AgentState) -> list[PlannedStep]:
    course_id = state.get("course_id") or ""
    extra = state.get("extra_inputs") or {}
    args = {
        "course_id": course_id,
        "exercise_id": extra.get("exercise_id", ""),
        "type": extra.get("type") or extra.get("exercise_type") or "single_choice",
        "answer": extra.get("answer", ""),
    }
    return [
        _step("grade_answer", args, description="单题评分"),
    ]


def _plan_lesson_plan(state: AgentState) -> list[PlannedStep]:
    """prepare-class skill 预设步骤（skills-spec §3.1）。"""

    user_input = state.get("user_input", "")
    course_id = state.get("course_id") or ""
    extra = state.get("extra_inputs") or {}
    chapter = str(extra.get("chapter_title") or _extract_chapter_title(user_input))
    duration = int(extra.get("duration_minutes") or _extract_int(user_input, 90))
    knowledge_points = extra.get("knowledge_points")

    steps: list[PlannedStep] = [
        _step(
            "search_kb",
            {"course_id": course_id, "query": chapter, "top_k": 8},
            description=f"检索章节 {chapter} 资料",
        ),
        _step(
            "lesson_outline",
            {
                "course_id": course_id,
                "chapter_title": chapter,
                "duration_minutes": duration,
                "knowledge_points": knowledge_points,
            },
            description=f"生成 {duration} 分钟讲解提纲",
        ),
    ]
    if extra.get("with_exercises", True):
        steps.append(
            _step(
                "generate_exercise",
                {
                    "course_id": course_id,
                    "count": 8,
                    "types": ["single_choice", "true_false", "fill_in_blank", "short_answer"],
                    "difficulty": "easy",
                    "knowledge_scope": knowledge_points,
                },
                description="配套生成 8 道课后练习",
            )
        )
    return steps


def _plan_recommend(state: AgentState) -> list[PlannedStep]:
    """personalized-practice skill 预设步骤（skills-spec §3.2）。"""

    course_id = state.get("course_id") or ""
    student_id = state.get("student_id") or state.get("user_id") or ""
    extra = state.get("extra_inputs") or {}
    count = int(extra.get("count") or 5)

    return [
        _step(
            "get_mastery",
            {
                "student_id": student_id,
                "course_id": course_id,
                "weak_threshold": float(extra.get("weak_threshold") or 0.6),
            },
            description="查询学生掌握度",
        ),
        _step(
            "generate_exercise",
            {
                "course_id": course_id,
                "count": count,
                "types": ["single_choice", "true_false", "fill_in_blank", "short_answer"],
                "difficulty": "easy",
                # 占位：tool_executor 执行完 get_mastery 后会回填 knowledge_scope
                "knowledge_scope": None,
            },
            description=f"针对薄弱知识点生成 {count} 道练习",
        ),
    ]


# ── LLM 兜底（mixed） ─────────────────────────────────────────────────


def _tool_catalog() -> str:
    lines = []
    for spec in REGISTRY.values():
        lines.append(f"- {spec.name}: {spec.description}")
    return "\n".join(lines)


def _plan_with_llm(state: AgentState) -> list[PlannedStep]:
    if not llm_available():
        return _plan_qa(state)

    user_input = state.get("user_input", "")
    course_id = state.get("course_id") or ""
    student_id = state.get("student_id") or state.get("user_id") or ""

    system_prompt = (
        "你是教学智能体的任务规划器。把用户请求拆解为 1-5 个有序工具调用步骤。"
        "只能使用下述工具，且必须严格输出 JSON。"
    )
    user_prompt = (
        f"可用工具：\n{_tool_catalog()}\n\n"
        f"上下文 course_id={course_id}; student_id={student_id};\n"
        f"用户请求：{user_input}\n\n"
        "返回 JSON 结构：\n"
        '{"steps": [{"tool": "<工具名>", "args": {...}, "description": "<本步目的>"}, ...]}\n'
        "要求：每个 args 必须可直接传给工具；step 数 1-5；前后步骤可隐式依赖（执行器会自动传值）。"
    )
    payload = call_json(system_prompt, user_prompt)
    if not isinstance(payload, dict):
        return _plan_qa(state)
    raw_steps = payload.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        return _plan_qa(state)

    steps: list[PlannedStep] = []
    for raw in raw_steps[:5]:
        if not isinstance(raw, dict):
            continue
        tool = str(raw.get("tool") or "").strip()
        if tool not in REGISTRY:
            continue
        args = raw.get("args") if isinstance(raw.get("args"), dict) else {}
        description = str(raw.get("description") or "")
        steps.append(_step(tool, args, description=description))
    return steps or _plan_qa(state)


# ── Repair plan based on reflector suggestion ─────────────────────────


def _apply_reflect_suggestion(state: AgentState, plan: list[PlannedStep]) -> list[PlannedStep]:
    history = state.get("reflect_history") or []
    if not history:
        return plan
    last = history[-1]
    failed = last.get("failed_dimensions") or []
    if "answer_grounded" in failed or "kp_match" in failed:
        for step in plan:
            if step.get("tool_name") == "search_kb":
                step["tool_args"]["top_k"] = min(
                    20, max(int(step["tool_args"].get("top_k") or 5) + 3, 8)
                )
                step["description"] = (step.get("description") or "") + "（反思后扩大检索）"
                break
    if "coverage" in failed:
        # 将 lesson_outline 的 knowledge_points 强制写入用户提示中的关键词
        user_input = state.get("user_input", "")
        for step in plan:
            if step.get("tool_name") == "lesson_outline":
                step["tool_args"].setdefault("knowledge_points", None)
                step["description"] = (step.get("description") or "") + "（反思后补充覆盖）"
    return plan


# ── 入口 ──────────────────────────────────────────────────────────────


_INTENT_PLANNERS = {
    Intent.QA.value: _plan_qa,
    Intent.EXERCISE_GEN.value: _plan_exercise_gen,
    Intent.EXERCISE_GRADE.value: _plan_exercise_grade,
    Intent.LESSON_PLAN.value: _plan_lesson_plan,
    Intent.RECOMMEND.value: _plan_recommend,
}


def planner_node(state: AgentState) -> dict:
    intent = state.get("intent") or Intent.QA.value
    builder = _INTENT_PLANNERS.get(intent)
    if builder:
        plan = builder(state)
    else:
        plan = _plan_with_llm(state)

    plan = _apply_reflect_suggestion(state, plan)

    plan_attempts = int(state.get("plan_attempts") or 0)

    logger.info(
        "planner: intent=%s steps=%s attempts=%s",
        intent,
        json.dumps([s["tool_name"] for s in plan], ensure_ascii=False),
        plan_attempts,
    )

    return {
        "plan": plan,
        "cursor": 0,
        "step_results": [],
        "plan_attempts": plan_attempts + 1,
    }
