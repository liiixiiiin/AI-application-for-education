import json
import os
from itertools import cycle
from typing import Iterable

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ..utils import generate_id, now_iso
from .knowledge_base import generate_knowledge_points, search_documents
from .langchain_client import get_chat_model, is_dashscope_configured
from .model_client import parse_json_payload


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_EXERCISE_ROOT = os.path.join(_PROJECT_ROOT, "data", "exercises")


def _ensure_course_exercise_dir(course_id: str) -> str:
    path = os.path.join(_EXERCISE_ROOT, course_id)
    os.makedirs(path, exist_ok=True)
    return path


def _iter_exercise_files(course_id: str) -> list[str]:
    dir_path = os.path.join(_EXERCISE_ROOT, course_id)
    if not os.path.exists(dir_path):
        return []
    return [
        os.path.join(dir_path, filename)
        for filename in os.listdir(dir_path)
        if filename.endswith(".json")
    ]


def _load_exercise_file(file_path: str) -> dict | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def save_exercise_batch(course_id: str, exercises: list[dict], title: str | None = None) -> dict:
    batch_id = generate_id("batch")
    dir_path = _ensure_course_exercise_dir(course_id)
    file_path = os.path.join(dir_path, f"{batch_id}.json")
    
    payload = {
        "batch_id": batch_id,
        "course_id": course_id,
        "title": title or f"练习批次 {now_iso()}",
        "created_at": now_iso(),
        "exercises": exercises,
        "updated_at": None,
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    return payload


def list_exercise_batches(course_id: str) -> list[dict]:
    batch_map: dict[str, dict] = {}
    for file_path in _iter_exercise_files(course_id):
        data = _load_exercise_file(file_path)
        if not data:
            continue
        batch_id = data.get("batch_id")
        if not batch_id:
            continue
        # Batch file format
        if isinstance(data.get("exercises"), list):
            count = len(data.get("exercises", []))
            batch_map[batch_id] = {
                "batch_id": batch_id,
                "title": data.get("title") or f"练习批次 {batch_id}",
                "created_at": data.get("created_at") or now_iso(),
                "count": count,
            }
            continue
        # Legacy single-exercise file format
        entry = batch_map.get(batch_id)
        created_at = data.get("created_at") or now_iso()
        if not entry:
            batch_map[batch_id] = {
                "batch_id": batch_id,
                "title": data.get("title") or f"练习批次 {batch_id}",
                "created_at": created_at,
                "count": 1,
            }
        else:
            entry["count"] += 1
            if created_at < entry["created_at"]:
                entry["created_at"] = created_at

    batches = list(batch_map.values())
    return sorted(batches, key=lambda x: x["created_at"], reverse=True)


def get_exercise_batch(course_id: str, batch_id: str) -> dict | None:
    file_path = os.path.join(_EXERCISE_ROOT, course_id, f"{batch_id}.json")
    if not os.path.exists(file_path):
        # Fallback: legacy single-exercise files
        exercises = []
        created_at = None
        for legacy_path in _iter_exercise_files(course_id):
            data = _load_exercise_file(legacy_path)
            if not data:
                continue
            if data.get("batch_id") != batch_id:
                continue
            exercises.append(data)
            if data.get("created_at") and (created_at is None or data["created_at"] < created_at):
                created_at = data["created_at"]
        if not exercises:
            return None
        return {
            "batch_id": batch_id,
            "course_id": course_id,
            "title": f"练习批次 {batch_id}",
            "created_at": created_at or now_iso(),
            "exercises": exercises,
            "updated_at": None,
        }
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_exercise_batch(course_id: str, batch_id: str, title: str | None = None, exercises: list[dict] | None = None) -> dict | None:
    file_path = os.path.join(_EXERCISE_ROOT, course_id, f"{batch_id}.json")
    if not os.path.exists(file_path):
        # Migrate legacy batch to new batch file
        legacy_batch = get_exercise_batch(course_id, batch_id)
        if not legacy_batch:
            return None
        if exercises is None:
            exercises = legacy_batch.get("exercises", [])
        payload = {
            "batch_id": batch_id,
            "course_id": course_id,
            "title": title or legacy_batch.get("title") or f"练习批次 {batch_id}",
            "created_at": legacy_batch.get("created_at") or now_iso(),
            "exercises": exercises,
            "updated_at": now_iso(),
        }
        _ensure_course_exercise_dir(course_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # Remove legacy single-exercise files for this batch
        for legacy_path in _iter_exercise_files(course_id):
            data = _load_exercise_file(legacy_path)
            if not data or data.get("batch_id") != batch_id:
                continue
            try:
                os.remove(legacy_path)
            except OSError:
                pass
        return payload
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if title is not None:
        data["title"] = title
    if exercises is not None:
        data["exercises"] = exercises
    
    data["updated_at"] = now_iso()
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data


def delete_exercise_batch(course_id: str, batch_id: str) -> bool:
    file_path = os.path.join(_EXERCISE_ROOT, course_id, f"{batch_id}.json")
    deleted = False
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            deleted = True
        except OSError:
            pass
    for legacy_path in _iter_exercise_files(course_id):
        data = _load_exercise_file(legacy_path)
        if not data or data.get("batch_id") != batch_id:
            continue
        try:
            os.remove(legacy_path)
            deleted = True
        except OSError:
            pass
    return deleted


def _get_saved_knowledge_points(course_id: str) -> list[str]:
    from ..db import get_connection

    conn = get_connection()
    rows = conn.execute(
        "SELECT point FROM knowledge_points WHERE course_id = ? ORDER BY created_at ASC",
        (course_id,),
    ).fetchall()
    conn.close()
    return [row["point"] for row in rows]


ALLOWED_TYPES = {"single_choice", "true_false", "short_answer"}


def _normalize_types(types: Iterable[str]) -> list[str]:
    cleaned = [item for item in types if item in ALLOWED_TYPES]
    return cleaned or ["single_choice"]


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

    # 优先使用用户提交的范围
    knowledge_points = [item for item in (knowledge_scope or []) if item]

    # 如果没传，尝试从数据库获取已保存的
    if not knowledge_points:
        knowledge_points = _get_saved_knowledge_points(course_id)

    # 如果数据库也没有，实时生成临时知识点
    if not knowledge_points:
        knowledge_points = generate_knowledge_points(course_id, limit=count)

    # 万能兜底
    if not knowledge_points:
        knowledge_points = ["核心知识点"]

    type_cycle = cycle(normalized_types)
    knowledge_cycle = cycle(knowledge_points)

    generated: list[dict] = []
    for index in range(count):
        exercise_type = next(type_cycle)
        knowledge_point = next(knowledge_cycle)
        chunk_id = f"chunk_{index + 1:03d}"
        results = search_documents(course_id, knowledge_point, top_k=2)
        source_chunks = (
            [result.get("chunk_id", chunk_id) for result in results[:1]] or [chunk_id]
        )
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

        if is_dashscope_configured() and results:
            model_payload = _generate_with_model(
                exercise_type,
                knowledge_point,
                difficulty,
                results,
            )
            if model_payload:
                _apply_model_payload(exercise, exercise_type, model_payload)

        generated.append(exercise)

    return generated


def _build_prompt(
    exercise_type: str,
    knowledge_point: str,
    difficulty: str,
    results: list[dict],
) -> tuple[str, str]:
    context_lines = []
    for idx, result in enumerate(results, start=1):
        context_lines.append(
            f"[{idx}] {result.get('title_path', '')}\n{result.get('content', '')}"
        )
    base_prompt = (
        "你是教学出题助手，请根据知识点与检索内容生成一道题目。"
        "返回严格 JSON，不要包含多余文本。"
    )
    type_prompt = {
        "single_choice": (
            "题型：单选题。字段：question, options(含key/text), answer, analysis。"
            "options 需包含 A/B/C/D 四项。"
        ),
        "true_false": "题型：判断题。字段：question, answer(true/false), analysis。",
        "short_answer": (
            "题型：简答题。字段：question, answer, rubric(数组包含point与score)。"
        ),
    }.get(exercise_type, "")

    context = "\n\n".join(context_lines)
    user_prompt = (
        f"难度：{difficulty}\n知识点：{knowledge_point}\n\n检索资料：\n{context}"
    )
    return f"{base_prompt}\n{type_prompt}", user_prompt


def _generate_with_model(
    exercise_type: str,
    knowledge_point: str,
    difficulty: str,
    results: list[dict],
) -> dict | None:
    llm = get_chat_model()
    if not llm:
        return None
    system_prompt, user_prompt = _build_prompt(
        exercise_type, knowledge_point, difficulty, results
    )
    
    # 修复 KeyError: 直接传入消息对象列表，绕过 ChatPromptTemplate 对 {} 的解析
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        text = getattr(response, "content", str(response))
        if not text:
            return None
        return parse_json_payload(text)
    except Exception:
        return None


def _build_short_answer_grading_prompt(
    question: str,
    answer: str,
    rubric_points: list[str],
    student_answer: str,
) -> tuple[str, str]:
    system_prompt = (
        "你是教学助教，请根据评分要点对简答题进行评测。"
        "输出严格 JSON，不要包含多余文本。"
    )
    rubric_text = "\n".join(f"- {point}" for point in rubric_points)
    user_prompt = (
        f"题目：{question}\n"
        f"参考答案：{answer}\n"
        f"评分要点：\n{rubric_text}\n\n"
        f"学生作答：{student_answer}\n\n"
        "请返回 JSON，字段：score(0-1), correct(true/false), feedback, suggestion, "
        "matched_points(array), missing_points(array)。"
    )
    return system_prompt, user_prompt


def _grade_short_answer_with_llm(
    question: str,
    answer: str,
    rubric_points: list[str],
    student_answer: str,
) -> dict | None:
    llm = get_chat_model()
    if not llm:
        return None
    system_prompt, user_prompt = _build_short_answer_grading_prompt(
        question, answer, rubric_points, student_answer
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    try:
        response = llm.invoke(messages)
        text = getattr(response, "content", str(response))
        if not text:
            return None
        payload = parse_json_payload(text)
        if not isinstance(payload, dict):
            return None
        return payload
    except Exception:
        return None


def _apply_model_payload(exercise: dict, exercise_type: str, payload: dict) -> None:
    question = payload.get("question")
    if isinstance(question, str) and question.strip():
        exercise["question"] = question.strip()

    if exercise_type == "single_choice":
        options = payload.get("options")
        if isinstance(options, list) and options:
            exercise["options"] = [
                {"key": item.get("key"), "text": item.get("text")}
                for item in options
                if isinstance(item, dict)
            ]
        answer = payload.get("answer")
        if isinstance(answer, str):
            exercise["answer"] = answer.strip().upper()
        analysis = payload.get("analysis")
        if isinstance(analysis, str):
            exercise["analysis"] = analysis.strip()
        return

    if exercise_type == "true_false":
        answer = payload.get("answer")
        normalized = _normalize_boolean(answer)
        if normalized is not None:
            exercise["answer"] = normalized
        analysis = payload.get("analysis")
        if isinstance(analysis, str):
            exercise["analysis"] = analysis.strip()
        return

    if exercise_type == "short_answer":
        answer = payload.get("answer")
        if isinstance(answer, str) and answer.strip():
            exercise["answer"] = answer.strip()
        rubric = payload.get("rubric")
        if isinstance(rubric, list):
            exercise["rubric"] = [
                {"point": item.get("point"), "score": item.get("score")}
                for item in rubric
                if isinstance(item, dict)
            ]


def grade_exercise(payload: dict) -> dict:
    exercise_type = payload.get("type")
    exercise_id = payload.get("exercise_id", "")
    course_id = payload.get("course_id", "")
    student_answer = payload.get("answer")

    # 尝试从该课程的所有批次中找到这道题，以获取标准答案
    correct_answer = None
    rubric = None
    question = None
    dir_path = os.path.join(_EXERCISE_ROOT, course_id)
    if os.path.exists(dir_path):
        for filename in os.listdir(dir_path):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(dir_path, filename), "r", encoding="utf-8") as f:
                        batch_data = json.load(f)
                        for ex in batch_data.get("exercises", []):
                            if ex.get("exercise_id") == exercise_id:
                                correct_answer = ex.get("answer")
                                rubric = ex.get("rubric")
                                question = ex.get("question")
                                break
                except Exception:
                    continue
            if correct_answer is not None:
                break

    if exercise_type == "single_choice":
        expected = str(correct_answer).strip().upper() if correct_answer else "B"
        normalized = str(student_answer).strip().upper() if student_answer is not None else ""
        correct = normalized == expected
        return {
            "exercise_id": exercise_id,
            "correct": correct,
            "score": 1 if correct else 0,
            "feedback": "回答正确。" if correct else f"答案不一致，正确选项是 {expected}。",
            "suggestion": "" if correct else "建议回顾该知识点的核心定义。",
        }

    if exercise_type == "true_false":
        expected = _normalize_boolean(correct_answer) if correct_answer is not None else True
        normalized = _normalize_boolean(student_answer)
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
        answer_text = str(student_answer).strip() if student_answer is not None else ""
        # 如果有标准评分要点，则使用
        rubric_points = [r.get("point") for r in rubric] if rubric else ["说明核心概念或定义", "描述应用场景或作用"]
        matched_points: list[str] = []
        missing_points: list[str] = []

        if answer_text and is_dashscope_configured():
            llm_payload = _grade_short_answer_with_llm(
                question or "",
                str(correct_answer or ""),
                rubric_points,
                answer_text,
            )
            if llm_payload:
                score = float(llm_payload.get("score", 0))
                correct = bool(llm_payload.get("correct", score >= 0.8))
                feedback = llm_payload.get("feedback") or "已完成评测。"
                suggestion = llm_payload.get("suggestion") or ""
                matched_points = llm_payload.get("matched_points") or []
                missing_points = llm_payload.get("missing_points") or []
                return {
                    "exercise_id": exercise_id,
                    "correct": correct,
                    "score": max(0, min(1, score)),
                    "feedback": feedback,
                    "suggestion": suggestion,
                    "matched_points": matched_points or None,
                    "missing_points": missing_points or None,
                }

        if answer_text:
            # 简单的关键词匹配逻辑（实际应用中应调用模型）
            for p in rubric_points:
                # 提取评分点中的关键名词/短语
                if any(kw in answer_text for kw in [p[:4], p[-4:]] if len(kw) > 1):
                    matched_points.append(p)
                else:
                    missing_points.append(p)
        else:
            missing_points = rubric_points.copy()

        score = round(len(matched_points) / len(rubric_points), 2) if rubric_points else 0
        correct = score >= 0.8
        if not answer_text:
            feedback = "回答为空或过短。"
            suggestion = "请补充完整描述，覆盖评分要点。"
        elif correct:
            feedback = "回答完整且准确。"
            suggestion = ""
        elif matched_points:
            feedback = "回答部分正确。"
            suggestion = f"还需补充：{', '.join(missing_points)}"
        else:
            feedback = "回答未命中关键要点。"
            suggestion = "建议重新阅读相关章节，关注定义与应用场景。"

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
