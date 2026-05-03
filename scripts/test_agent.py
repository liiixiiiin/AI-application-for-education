"""Smoke test for the LangGraph Agent (P0-1)。

运行方式：
  cd <项目根>
  backend/venv/bin/python scripts/test_agent.py

可选环境变量：
  DASHSCOPE_API_KEY        启用 LLM 路径（不设置则走规则兜底）
  AGENT_TEST_COURSE_ID     指定课程 ID（不设置时自动选数据库里第一个课程）
  AGENT_TEST_STUDENT_ID    指定学生 ID（不设置时使用占位用户）

脚本对每个意图运行一条用例，打印：意图、Skill、计划、各步骤结果摘要、
反思结论、最终 answer 摘要。意图识别命中率与最终是否 degraded 会汇总。
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.agents import run_agent  # noqa: E402
from app.db import get_connection, init_db  # noqa: E402

CASES = [
    {
        "id": "qa_01",
        "label": "QA 基础问答",
        "user_input": "RAG 中 Rerank 的作用是什么？",
        "expected_intent": "qa",
        "expected_tools": ["search_kb"],
    },
    {
        "id": "qa_02",
        "label": "QA 概念解释",
        "user_input": "什么是 LangGraph？请简述其状态机模型。",
        "expected_intent": "qa",
        "expected_tools": ["search_kb"],
    },
    {
        "id": "exgen_01",
        "label": "出题：单选 + 判断",
        "user_input": "请帮我出 5 道单选和判断题，难度简单。",
        "expected_intent": "exercise_gen",
        "expected_tools": ["generate_exercise"],
    },
    {
        "id": "lesson_01",
        "label": "备课：90 分钟",
        "user_input": "帮我准备 RAG 那一章的课，90 分钟。",
        "expected_intent": "lesson_plan",
        "expected_skill": "prepare-class",
        "expected_tools": ["search_kb", "lesson_outline", "generate_exercise"],
    },
    {
        "id": "recommend_01",
        "label": "个性化推荐",
        "user_input": "我哪里弱？请推荐针对性练习。",
        "expected_intent": "recommend",
        "expected_skill": "personalized-practice",
        "expected_tools": ["get_mastery", "generate_exercise"],
    },
    {
        "id": "grade_01",
        "label": "评分（缺数据时降级）",
        "user_input": "判一下我的答案。",
        "expected_intent": "exercise_grade",
        "expected_skill": "grade-essay",
        "expected_tools": ["grade_answer"],
        "extra_inputs": {
            "exercise_id": "ex_smoketest_dummy",
            "type": "single_choice",
            "answer": "B",
        },
    },
]


def _pick_course_id() -> str | None:
    forced = os.getenv("AGENT_TEST_COURSE_ID")
    if forced:
        return forced
    try:
        init_db()
        conn = get_connection()
        row = conn.execute(
            "SELECT id FROM courses ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        conn.close()
        return row["id"] if row else None
    except Exception as exc:
        print(f"[warn] cannot pick course: {exc}")
        return None


def _short(payload, length: int = 240) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=False, default=str)
    except Exception:
        text = str(payload)
    return text if len(text) <= length else text[:length] + "..."


def main() -> int:
    course_id = _pick_course_id()
    student_id = os.getenv("AGENT_TEST_STUDENT_ID") or "user_smoketest"

    print(f"\n=== Agent Smoke Test (P0-1) ===")
    print(f"course_id={course_id}  student_id={student_id}")
    print(f"DASHSCOPE_API_KEY={'set' if os.getenv('DASHSCOPE_API_KEY') else 'unset (rule fallback)'}\n")

    intent_hits = 0
    tool_hits = 0
    successes = 0

    for case in CASES:
        print(f"--- [{case['id']}] {case['label']} ---")
        started = time.time()
        try:
            result = run_agent(
                user_input=case["user_input"],
                course_id=course_id,
                user_id=student_id,
                extra_inputs=case.get("extra_inputs"),
                time_budget_seconds=45.0,
            )
        except Exception as exc:
            print(f"  ✗ exception: {exc}\n")
            continue

        actual_intent = result.get("intent")
        actual_skill = result.get("skill")
        actual_tools = [step.get("tool") for step in result.get("steps") or []]
        intent_ok = actual_intent == case.get("expected_intent")
        intent_hits += int(intent_ok)
        expected_tools = case.get("expected_tools") or []
        tool_overlap = any(t in actual_tools for t in expected_tools) if expected_tools else True
        tool_hits += int(tool_overlap)
        success = bool(result.get("answer")) and not result.get("error")
        successes += int(success)

        print(f"  intent      = {actual_intent}  ({'OK' if intent_ok else 'MISS, expected ' + str(case.get('expected_intent'))})")
        if case.get("expected_skill"):
            skill_ok = actual_skill == case["expected_skill"]
            print(f"  skill       = {actual_skill}  ({'OK' if skill_ok else 'MISS, expected ' + case['expected_skill']})")
        else:
            print(f"  skill       = {actual_skill}")
        print(f"  tools       = {actual_tools}")
        print(f"  steps_ok    = {[step.get('success') for step in result.get('steps') or []]}")
        print(f"  reflect     = {[v.get('failed_dimensions') for v in result.get('reflect_history') or []]}")
        print(f"  degraded    = {result.get('degraded')}")
        print(f"  duration_ms = {result.get('duration_ms')}  wall={int((time.time()-started)*1000)}ms")
        print(f"  answer      = {_short(result.get('answer'))}\n")

    total = len(CASES)
    print("=== Summary ===")
    print(f"intent hit : {intent_hits}/{total}  ({intent_hits/total:.0%})")
    print(f"tool hit   : {tool_hits}/{total}  ({tool_hits/total:.0%})")
    print(f"success    : {successes}/{total}  ({successes/total:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
