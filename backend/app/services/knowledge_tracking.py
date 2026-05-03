import json
import logging

from ..db import get_connection
from ..utils import generate_id, now_iso
from .exercises import generate_exercises

logger = logging.getLogger(__name__)

EMA_ALPHA = 0.3
WEAK_THRESHOLD = 0.6
DEFAULT_MASTERY = 0.5


def record_attempt(
    student_id: str,
    exercise_id: str,
    course_id: str,
    score: float,
    knowledge_points: list[str],
) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO exercise_attempts (id, student_id, exercise_id, course_id, score, knowledge_points, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                generate_id("att"),
                student_id,
                exercise_id,
                course_id,
                score,
                json.dumps(knowledge_points, ensure_ascii=False),
                now_iso(),
            ),
        )

        ts = now_iso()
        for kp in knowledge_points:
            row = conn.execute(
                "SELECT mastery, attempt_count FROM knowledge_mastery "
                "WHERE student_id = ? AND course_id = ? AND knowledge_point = ?",
                (student_id, course_id, kp),
            ).fetchone()

            if row:
                old_mastery = row["mastery"]
                new_mastery = EMA_ALPHA * score + (1 - EMA_ALPHA) * old_mastery
                conn.execute(
                    "UPDATE knowledge_mastery SET mastery = ?, attempt_count = attempt_count + 1, updated_at = ? "
                    "WHERE student_id = ? AND course_id = ? AND knowledge_point = ?",
                    (round(new_mastery, 4), ts, student_id, course_id, kp),
                )
            else:
                new_mastery = EMA_ALPHA * score + (1 - EMA_ALPHA) * DEFAULT_MASTERY
                conn.execute(
                    "INSERT INTO knowledge_mastery (id, student_id, course_id, knowledge_point, mastery, attempt_count, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, 1, ?)",
                    (generate_id("km"), student_id, course_id, kp, round(new_mastery, 4), ts),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to record attempt")
        raise
    finally:
        conn.close()


def get_knowledge_state(student_id: str, course_id: str) -> dict:
    conn = get_connection()

    rows = conn.execute(
        "SELECT knowledge_point, mastery, attempt_count, updated_at "
        "FROM knowledge_mastery WHERE student_id = ? AND course_id = ? "
        "ORDER BY mastery ASC",
        (student_id, course_id),
    ).fetchall()

    tracked = {row["knowledge_point"] for row in rows}

    all_kp_rows = conn.execute(
        "SELECT point FROM knowledge_points WHERE course_id = ? ORDER BY created_at ASC",
        (course_id,),
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        items.append({
            "knowledge_point": row["knowledge_point"],
            "mastery": row["mastery"],
            "attempt_count": row["attempt_count"],
            "updated_at": row["updated_at"],
        })

    for kp_row in all_kp_rows:
        if kp_row["point"] not in tracked:
            items.append({
                "knowledge_point": kp_row["point"],
                "mastery": DEFAULT_MASTERY,
                "attempt_count": 0,
                "updated_at": "",
            })

    items.sort(key=lambda x: x["mastery"])
    weak_points = [item["knowledge_point"] for item in items if item["mastery"] < WEAK_THRESHOLD]

    return {
        "course_id": course_id,
        "items": items,
        "weak_points": weak_points,
    }


def get_weak_points(student_id: str, course_id: str, threshold: float = WEAK_THRESHOLD) -> list[str]:
    state = get_knowledge_state(student_id, course_id)
    return [item["knowledge_point"] for item in state["items"] if item["mastery"] < threshold]


def generate_recommended_exercises(
    student_id: str,
    course_id: str,
    count: int = 5,
    difficulty: str = "easy",
) -> list[dict]:
    state = get_knowledge_state(student_id, course_id)
    weak = [item["knowledge_point"] for item in state["items"] if item["mastery"] < WEAK_THRESHOLD]

    if not weak:
        sorted_items = [item for item in state["items"] if item["attempt_count"] > 0]
        sorted_items.sort(key=lambda x: x["mastery"])
        weak = [item["knowledge_point"] for item in sorted_items[:max(3, count)]]

    if not weak:
        weak = None

    types = ["single_choice", "true_false", "fill_in_blank", "short_answer"]
    return generate_exercises(
        course_id=course_id,
        count=count,
        types=types,
        difficulty=difficulty,
        knowledge_scope=weak,
    )


def get_exercise_attempts(student_id: str, course_id: str, limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, exercise_id, course_id, score, knowledge_points, created_at "
        "FROM exercise_attempts WHERE student_id = ? AND course_id = ? "
        "ORDER BY created_at DESC LIMIT ?",
        (student_id, course_id, limit),
    ).fetchall()
    conn.close()

    results = []
    for row in rows:
        kps = row["knowledge_points"]
        try:
            kps_list = json.loads(kps) if isinstance(kps, str) else kps
        except (json.JSONDecodeError, TypeError):
            kps_list = []
        results.append({
            "id": row["id"],
            "exercise_id": row["exercise_id"],
            "course_id": row["course_id"],
            "score": row["score"],
            "knowledge_points": kps_list,
            "created_at": row["created_at"],
        })
    return results
