from itertools import cycle
from typing import Iterable

from ..utils import generate_id
from .knowledge_base import search_documents


ALLOWED_TYPES = {"single_choice", "true_false", "short_answer"}


def _normalize_types(types: Iterable[str]) -> list[str]:
    cleaned = [item for item in types if item in ALLOWED_TYPES]
    return cleaned or ["single_choice"]


def _build_source_chunks(course_id: str, keyword: str, fallback_id: str) -> list[str]:
    results = search_documents(course_id, keyword, top_k=1)
    if results:
        return [results[0].get("chunk_id", fallback_id)]
    return [fallback_id]


def _normalize_boolean(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return None


def generate_exercises(
    course_id: str,
    count: int,
    types: list[str],
    difficulty: str,
    knowledge_scope: list[str] | None,
) -> list[dict]:
    normalized_types = _normalize_types(types)
    knowledge_points = [item for item in (knowledge_scope or []) if item] or ["核心知识点"]
    type_cycle = cycle(normalized_types)
    knowledge_cycle = cycle(knowledge_points)

    generated: list[dict] = []
    for index in range(count):
        exercise_type = next(type_cycle)
        knowledge_point = next(knowledge_cycle)
        chunk_id = f"chunk_{index + 1:03d}"
        source_chunks = _build_source_chunks(course_id, knowledge_point, chunk_id)
        exercise = {
            "exercise_id": generate_id("ex"),
            "course_id": course_id,
            "type": exercise_type,
            "question": f"关于“{knowledge_point}”的描述，哪一项最准确？",
            "knowledge_points": [knowledge_point],
            "source_chunks": source_chunks,
            "difficulty": difficulty,
        }

        if exercise_type == "single_choice":
            exercise.update(
                {
                    "options": [
                        {"key": "A", "text": f"{knowledge_point}是固定不变的规则。"},
                        {"key": "B", "text": f"{knowledge_point}用于定义核心概念或约束。"},
                        {"key": "C", "text": f"{knowledge_point}仅用于性能优化。"},
                        {"key": "D", "text": f"{knowledge_point}与课程无直接关系。"},
                    ],
                    "answer": "B",
                    "analysis": "占位解析：基于课程知识库的核心概念进行归纳。",
                }
            )
        elif exercise_type == "true_false":
            exercise.update(
                {
                    "answer": True,
                    "analysis": "占位解析：该说法与知识点核心定义一致。",
                }
            )
        elif exercise_type == "short_answer":
            exercise.update(
                {
                    "answer": f"{knowledge_point}用于说明课程中的关键概念与应用场景。",
                    "rubric": [
                        {"point": f"说明{knowledge_point}的定义或作用", "score": 0.6},
                        {"point": "结合课程场景举例", "score": 0.4},
                    ],
                }
            )

        generated.append(exercise)

    return generated


def grade_exercise(payload: dict) -> dict:
    exercise_type = payload.get("type")
    exercise_id = payload.get("exercise_id", "")
    answer = payload.get("answer")

    if exercise_type == "single_choice":
        expected = "B"
        normalized = str(answer).strip().upper() if answer is not None else ""
        correct = normalized == expected
        return {
            "exercise_id": exercise_id,
            "correct": correct,
            "score": 1 if correct else 0,
            "feedback": "回答正确。" if correct else f"答案不一致，正确选项是 {expected}。",
            "suggestion": "" if correct else "建议回顾该知识点的核心定义。",
        }

    if exercise_type == "true_false":
        expected = True
        normalized = _normalize_boolean(answer)
        if normalized is None:
            return {
                "exercise_id": exercise_id,
                "correct": False,
                "score": 0,
                "feedback": "未识别的判断题答案，请提交 true/false。",
                "suggestion": "请确认答案格式后重新提交。",
            }
        correct = normalized == expected
        return {
            "exercise_id": exercise_id,
            "correct": correct,
            "score": 1 if correct else 0,
            "feedback": "回答正确。" if correct else "判断结果不正确，请对照知识点再确认。",
            "suggestion": "" if correct else "建议回顾判断依据与相关定义。",
        }

    if exercise_type == "short_answer":
        answer_text = str(answer).strip() if answer is not None else ""
        rubric_points = ["说明核心概念或定义", "描述应用场景或作用"]
        matched_points: list[str] = []
        missing_points: list[str] = []

        if answer_text:
            if any(token in answer_text for token in ["定义", "概念"]):
                matched_points.append(rubric_points[0])
            else:
                missing_points.append(rubric_points[0])

            if any(token in answer_text for token in ["作用", "应用", "场景"]):
                matched_points.append(rubric_points[1])
            else:
                missing_points.append(rubric_points[1])
        else:
            missing_points = rubric_points.copy()

        score = round(len(matched_points) / len(rubric_points), 2) if rubric_points else 0
        correct = score == 1
        if not answer_text:
            feedback = "回答为空或过短。"
            suggestion = "请补充完整描述，覆盖定义与应用场景。"
        elif correct:
            feedback = "回答完整。"
            suggestion = ""
        elif matched_points:
            feedback = "回答部分正确。"
            suggestion = "请补充缺失的关键要点。"
        else:
            feedback = "回答缺少关键要点。"
            suggestion = "建议从定义与应用场景两方面展开。"

        return {
            "exercise_id": exercise_id,
            "correct": correct,
            "score": score,
            "feedback": feedback,
            "suggestion": suggestion,
            "matched_points": matched_points or None,
            "missing_points": missing_points or None,
        }

    return {
        "exercise_id": exercise_id,
        "correct": False,
        "score": 0,
        "feedback": "题型不支持，无法评测。",
        "suggestion": "请确认题型后重新提交。",
    }
