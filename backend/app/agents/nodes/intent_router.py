"""意图识别节点（agent-spec §3.1）。

输入：state.user_input（+ 可选对话上下文摘要）
输出：state.intent（标签）+ state.skill（默认绑定 skill）

策略：
1. 优先调用 LLM 做结构化分类
2. LLM 不可用或解析失败时，落到关键词规则兜底
"""

from __future__ import annotations

import logging
import re

from ..intents import ALL_INTENTS, INTENT_DESCRIPTIONS, Intent, get_default_skill
from ..llm import call_json, llm_available
from ..state import AgentState

logger = logging.getLogger(__name__)


_RULE_PATTERNS: list[tuple[str, list[str]]] = [
    (
        Intent.LESSON_PLAN.value,
        [
            "备课",
            "备一节课",
            "教案",
            "讲解提纲",
            "备一章",
            "课件大纲",
            "准备一节课",
            "备课提纲",
            "讲课大纲",
            "教学大纲",
            "教学设计",
        ],
    ),
    (
        Intent.RECOMMEND.value,
        ["推荐", "薄弱", "针对性练习", "个性化", "我哪里弱", "弱项", "弱点"],
    ),
    (
        Intent.EXERCISE_GRADE.value,
        ["判一下", "评一下", "批改", "我的答案", "改作业", "评分", "打分"],
    ),
    (
        Intent.EXERCISE_GEN.value,
        ["出题", "出几道", "出 ", "出一道", "出一组", "出 5", "出5", "练习题", "测验题", "考核题"],
    ),
]


_LESSON_PHRASE_PATTERN = re.compile(r"(准备|讲|做)[^，。,.]*?(课|章节|这一章|那一章)")
_DURATION_PATTERN = re.compile(r"\d+\s*(分钟|min|课时)")


def _rule_classify(user_input: str) -> str:
    text = user_input.strip()
    for intent, keywords in _RULE_PATTERNS:
        for kw in keywords:
            if kw in text:
                return intent

    if _LESSON_PHRASE_PATTERN.search(text) and (
        _DURATION_PATTERN.search(text) or "课" in text or "章" in text
    ):
        return Intent.LESSON_PLAN.value

    if re.search(r"(总结|并|然后|和).+(出|生成).+题", text):
        return Intent.MIXED.value
    if text:
        return Intent.QA.value
    return Intent.UNKNOWN.value


def _llm_classify(user_input: str) -> tuple[str, str | None] | None:
    desc_lines = "\n".join(
        f"- {label}: {INTENT_DESCRIPTIONS[label]}" for label in ALL_INTENTS
    )
    system_prompt = (
        "你是教学智能体的意图识别器。"
        "根据用户原始请求选择最合适的意图标签，并返回 JSON。"
        "若用户请求同时包含多种意图（如先答疑再出题），返回 mixed。"
    )
    user_prompt = (
        "可选意图标签及其含义：\n"
        f"{desc_lines}\n\n"
        f"用户请求：{user_input}\n\n"
        '请仅返回 JSON：{"intent": "<标签>", "skill": "<skill 名 或 null>", "reason": "<一句话理由>"}。'
        "skill 字段仅在该意图有默认 skill 时填写（lesson_plan→prepare-class，"
        "recommend→personalized-practice，exercise_grade→grade-essay），其他情况填 null。"
    )
    payload = call_json(system_prompt, user_prompt)
    if not payload:
        return None
    intent = str(payload.get("intent") or "").strip()
    if intent not in ALL_INTENTS:
        return None
    skill = payload.get("skill")
    skill = str(skill).strip() if skill and str(skill).strip().lower() != "null" else None
    return intent, skill


def intent_router_node(state: AgentState) -> dict:
    user_input = (state.get("user_input") or "").strip()
    if not user_input:
        return {"intent": Intent.UNKNOWN.value, "skill": None}

    intent: str = ""
    skill: str | None = None

    if llm_available():
        try:
            llm_result = _llm_classify(user_input)
        except Exception:
            logger.exception("intent_router LLM classify failed")
            llm_result = None
        if llm_result:
            intent, skill = llm_result

    if not intent:
        intent = _rule_classify(user_input)

    if intent == Intent.UNKNOWN.value:
        intent = Intent.QA.value

    if not skill:
        skill = get_default_skill(intent)

    logger.info("intent_router: intent=%s skill=%s", intent, skill)
    return {"intent": intent, "skill": skill}
