"""Tool 注册表（agent-spec §6）。

每个工具定义：
- name：工具名（与 MCP Server / Skill 中保持一致）
- description：LLM 路由依据
- input_schema：Pydantic 模型，参数校验
- runner：实际执行函数（接受 dict，返回 dict）
- summary_keys：从结果中抽取展示字段，用于 step.result_summary

工具实现仅做"薄包装"：调用 backend/app/services/* 现有函数，
不重写业务，业务异常向上抛出由 tool_executor 捕获。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, Field, ValidationError

from ...services import exercises as exercises_service
from ...services import knowledge_base as kb_service
from ...services import knowledge_tracking as kt_service
from ...services import lesson_plans as lesson_service

logger = logging.getLogger(__name__)


# ── Pydantic input schemas ────────────────────────────────────────────


class SearchKbArgs(BaseModel):
    course_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] | None = None


class LessonOutlineArgs(BaseModel):
    course_id: str = Field(min_length=1)
    chapter_title: str = Field(min_length=1)
    duration_minutes: int = Field(default=90, ge=10, le=240)
    knowledge_points: list[str] | None = None
    audience_level: str = "基础"
    include_practice: bool = True


class GenerateExerciseArgs(BaseModel):
    course_id: str = Field(min_length=1)
    count: int = Field(default=5, ge=1, le=20)
    types: list[str] = Field(default_factory=lambda: ["single_choice"])
    difficulty: str = "easy"
    knowledge_scope: list[str] | None = None


class GradeAnswerArgs(BaseModel):
    exercise_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    answer: Any


class GetMasteryArgs(BaseModel):
    student_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    weak_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class WebSearchArgs(BaseModel):
    course_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


# ── Tool runners ──────────────────────────────────────────────────────


def _run_search_kb(args: dict[str, Any]) -> dict[str, Any]:
    parsed = SearchKbArgs(**args)
    results = kb_service.search_documents(
        parsed.course_id, parsed.query, parsed.top_k, parsed.filters,
    )
    return {"results": results, "count": len(results)}


def _run_lesson_outline(args: dict[str, Any]) -> dict[str, Any]:
    parsed = LessonOutlineArgs(**args)
    outline = lesson_service.generate_lesson_outline(
        course_id=parsed.course_id,
        chapter_title=parsed.chapter_title,
        duration_minutes=parsed.duration_minutes,
        knowledge_scope=parsed.knowledge_points,
        audience_level=parsed.audience_level,
        include_practice=parsed.include_practice,
    )
    return outline


def _run_generate_exercise(args: dict[str, Any]) -> dict[str, Any]:
    parsed = GenerateExerciseArgs(**args)
    generated = exercises_service.generate_exercises(
        course_id=parsed.course_id,
        count=parsed.count,
        types=parsed.types,
        difficulty=parsed.difficulty,
        knowledge_scope=parsed.knowledge_scope,
    )
    return {"generated": generated, "count": len(generated)}


def _run_grade_answer(args: dict[str, Any]) -> dict[str, Any]:
    parsed = GradeAnswerArgs(**args)
    payload = {
        "exercise_id": parsed.exercise_id,
        "course_id": parsed.course_id,
        "type": parsed.type,
        "answer": parsed.answer,
    }
    return exercises_service.grade_exercise(payload)


def _run_get_mastery(args: dict[str, Any]) -> dict[str, Any]:
    parsed = GetMasteryArgs(**args)
    state = kt_service.get_knowledge_state(parsed.student_id, parsed.course_id)
    items = state.get("items", [])
    threshold = parsed.weak_threshold
    return {
        "course_id": state.get("course_id"),
        "items": items,
        "weak_points": [
            item["knowledge_point"]
            for item in items
            if item.get("mastery", 1.0) < threshold
        ],
    }


def _run_web_search(args: dict[str, Any]) -> dict[str, Any]:
    """联网搜索：当前直接复用 RAG QA 链路 + DashScope enable_search。

    P0-2 上线 MCP Server 后改为 mcp_web_search 客户端调用。
    """

    parsed = WebSearchArgs(**args)
    from ...services.rag_qa import answer_question

    payload = answer_question(
        course_id=parsed.course_id,
        question=parsed.query,
        top_k=parsed.top_k,
        use_web_search=True,
    )
    return payload


# ── Result summary helpers ────────────────────────────────────────────


def _summarize_search_kb(result: dict[str, Any]) -> str:
    return f"命中 {result.get('count', 0)} 条片段"


def _summarize_lesson_outline(result: dict[str, Any]) -> str:
    flow = result.get("teaching_flow") or []
    kp = result.get("key_points") or []
    return f"提纲 {len(flow)} 模块 / {len(kp)} 知识点"


def _summarize_generate_exercise(result: dict[str, Any]) -> str:
    return f"生成 {result.get('count', 0)} 道题"


def _summarize_grade_answer(result: dict[str, Any]) -> str:
    score = result.get("score")
    correct = result.get("correct")
    score_text = f"{score:.2f}" if isinstance(score, (int, float)) else "n/a"
    return f"评分 {score_text}（{'正确' if correct else '不正确'}）"


def _summarize_get_mastery(result: dict[str, Any]) -> str:
    items = result.get("items") or []
    weak = result.get("weak_points") or []
    return f"知识点 {len(items)} 个 / 薄弱 {len(weak)} 个"


def _summarize_web_search(result: dict[str, Any]) -> str:
    citations = result.get("citations") or []
    return f"联网回答（{len(citations)} 条引用）"


# ── ToolSpec ──────────────────────────────────────────────────────────


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: type[BaseModel]
    runner: Callable[[dict[str, Any]], dict[str, Any]]
    summarizer: Callable[[dict[str, Any]], str]
    output_required_fields: list[str] = field(default_factory=list)

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.input_schema(**(args or {})).model_dump()
        except ValidationError as exc:
            raise ValueError(f"工具 {self.name} 参数校验失败：{exc}") from exc

    def call(self, args: dict[str, Any]) -> dict[str, Any]:
        validated = self.validate_args(args)
        return self.runner(validated)

    def summary(self, result: Any) -> str:
        try:
            if isinstance(result, dict):
                return self.summarizer(result)
        except Exception:  # noqa: BLE001 — summary 失败不应中断主流程
            logger.exception("Summary failed for tool %s", self.name)
        return str(result)[:120]


REGISTRY: dict[str, ToolSpec] = {
    "search_kb": ToolSpec(
        name="search_kb",
        description=(
            "课程知识库混合检索（向量 + BM25 + Rerank）。"
            "需要 course_id + query；返回 results 数组（含 chunk_id / content / source_doc_name 等）。"
        ),
        input_schema=SearchKbArgs,
        runner=_run_search_kb,
        summarizer=_summarize_search_kb,
        output_required_fields=["results", "count"],
    ),
    "lesson_outline": ToolSpec(
        name="lesson_outline",
        description=(
            "基于课程资料生成章节讲解提纲（教学目标 / 重难点 / 课堂流程 / 实训任务 / 考核建议）。"
            "用于备课场景。"
        ),
        input_schema=LessonOutlineArgs,
        runner=_run_lesson_outline,
        summarizer=_summarize_lesson_outline,
        output_required_fields=["objectives", "key_points", "teaching_flow"],
    ),
    "generate_exercise": ToolSpec(
        name="generate_exercise",
        description=(
            "按题型/难度/知识点范围批量生成练习题（单选/判断/填空/简答）。"
            "返回 generated 数组，每题含 question / answer / source_chunks 等。"
        ),
        input_schema=GenerateExerciseArgs,
        runner=_run_generate_exercise,
        summarizer=_summarize_generate_exercise,
        output_required_fields=["generated"],
    ),
    "grade_answer": ToolSpec(
        name="grade_answer",
        description=(
            "对单道练习题作答进行评分（客观题规则匹配 / 主观题大模型加权评分）。"
            "返回 score(0-1) + feedback + suggestion。"
        ),
        input_schema=GradeAnswerArgs,
        runner=_run_grade_answer,
        summarizer=_summarize_grade_answer,
        output_required_fields=["exercise_id", "score"],
    ),
    "get_mastery": ToolSpec(
        name="get_mastery",
        description=(
            "查询学生在指定课程下所有知识点的掌握度（EMA），"
            "返回 items 数组与 weak_points（mastery < weak_threshold 的知识点）。"
        ),
        input_schema=GetMasteryArgs,
        runner=_run_get_mastery,
        summarizer=_summarize_get_mastery,
        output_required_fields=["items"],
    ),
    "web_search": ToolSpec(
        name="web_search",
        description=(
            "DashScope 联网搜索增强问答，仅在用户明确要求或本地知识库覆盖不足时使用。"
        ),
        input_schema=WebSearchArgs,
        runner=_run_web_search,
        summarizer=_summarize_web_search,
        output_required_fields=["answer"],
    ),
}


def get_tool(name: str) -> ToolSpec | None:
    return REGISTRY.get(name)


def list_tool_specs() -> list[ToolSpec]:
    return list(REGISTRY.values())


def summarize_result(tool_name: str, result: Any) -> str:
    spec = REGISTRY.get(tool_name)
    if not spec:
        return str(result)[:120]
    return spec.summary(result)
