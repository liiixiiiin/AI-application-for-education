"""意图标签与默认 Skill 绑定（agent-spec §4）。"""

from __future__ import annotations

from enum import Enum
from typing import Final


class Intent(str, Enum):
    QA = "qa"
    EXERCISE_GEN = "exercise_gen"
    EXERCISE_GRADE = "exercise_grade"
    LESSON_PLAN = "lesson_plan"
    RECOMMEND = "recommend"
    MIXED = "mixed"
    UNKNOWN = "unknown"


ALL_INTENTS: Final[list[str]] = [item.value for item in Intent]


INTENT_DEFAULT_SKILL: Final[dict[str, str | None]] = {
    Intent.QA.value: None,
    Intent.EXERCISE_GEN.value: None,
    Intent.EXERCISE_GRADE.value: "grade-essay",
    Intent.LESSON_PLAN.value: "prepare-class",
    Intent.RECOMMEND.value: "personalized-practice",
    Intent.MIXED.value: None,
    Intent.UNKNOWN.value: None,
}


INTENT_DESCRIPTIONS: Final[dict[str, str]] = {
    Intent.QA.value: "知识问答：用户提出概念/原理/解释类问题，需要基于课程知识库给出回答。",
    Intent.EXERCISE_GEN.value: "出题：用户希望生成单选/判断/填空/简答练习题。",
    Intent.EXERCISE_GRADE.value: "评分：用户提交了某道题的作答，希望批改与点评。",
    Intent.LESSON_PLAN.value: "备课：用户希望生成章节讲解提纲、教学流程、实训任务等备课产出。",
    Intent.RECOMMEND.value: "个性化推荐：用户希望根据自己的薄弱知识点推荐针对性练习。",
    Intent.MIXED.value: "复合任务：单条请求同时包含问答/出题/备课等多种意图，需多步拆解。",
    Intent.UNKNOWN.value: "未匹配任何标签，按 qa 兜底走 RAG 链路。",
}


def get_default_skill(intent: str) -> str | None:
    return INTENT_DEFAULT_SKILL.get(intent)
