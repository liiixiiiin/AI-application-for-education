from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_teacher, require_user
from ..db import get_connection
from ..schemas import (
    CourseCreateRequest,
    CourseResponse,
    KnowledgePointResponse,
    KnowledgePointCreateRequest,
    KnowledgePointsSyncRequest,
)
from ..utils import generate_id, now_iso


router = APIRouter(prefix="/api/v1/courses", tags=["courses"])


def _row_to_course(row) -> CourseResponse:
    return CourseResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        creator_id=row["creator_id"],
        created_at=row["created_at"],
    )


@router.get("", response_model=dict)
def list_courses(user: dict = Depends(require_user)) -> dict:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM courses ORDER BY created_at DESC").fetchall()
    conn.close()
    courses = [_row_to_course(row).model_dump() for row in rows]
    return {"data": courses, "meta": {"count": len(courses)}}


@router.get("/{course_id}", response_model=dict)
def get_course(course_id: str, user: dict = Depends(require_user)) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"data": _row_to_course(row).model_dump(), "meta": {}}


@router.post("", response_model=dict)
def create_course(
    payload: CourseCreateRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    course_id = generate_id("course")
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO courses (id, title, description, creator_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (course_id, payload.title, payload.description, user["id"], now_iso()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    conn.close()
    return {"data": _row_to_course(row).model_dump(), "meta": {}}


@router.get("/{course_id}/knowledge-points", response_model=dict)
def list_knowledge_points(course_id: str, user: dict = Depends(require_user)) -> dict:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM knowledge_points WHERE course_id = ? ORDER BY created_at ASC",
        (course_id,),
    ).fetchall()
    conn.close()
    points = [
        KnowledgePointResponse(
            id=row["id"],
            course_id=row["course_id"],
            point=row["point"],
            created_at=row["created_at"],
        ).model_dump()
        for row in rows
    ]
    return {"data": points, "meta": {"count": len(points)}}


@router.post("/{course_id}/knowledge-points", response_model=dict)
def add_knowledge_point(
    course_id: str,
    payload: KnowledgePointCreateRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    point_id = generate_id("kp")
    conn = get_connection()
    conn.execute(
        "INSERT INTO knowledge_points (id, course_id, point, created_at) VALUES (?, ?, ?, ?)",
        (point_id, course_id, payload.point, now_iso()),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM knowledge_points WHERE id = ?", (point_id,)
    ).fetchone()
    conn.close()
    return {
        "data": KnowledgePointResponse(
            id=row["id"],
            course_id=row["course_id"],
            point=row["point"],
            created_at=row["created_at"],
        ).model_dump(),
        "meta": {},
    }


@router.post("/{course_id}/knowledge-points/sync", response_model=dict)
def sync_knowledge_points(
    course_id: str,
    payload: KnowledgePointsSyncRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    conn = get_connection()
    if payload.mode == "replace":
        conn.execute("DELETE FROM knowledge_points WHERE course_id = ?", (course_id,))

    now = now_iso()
    for point in payload.points:
        point_id = generate_id("kp")
        conn.execute(
            "INSERT INTO knowledge_points (id, course_id, point, created_at) VALUES (?, ?, ?, ?)",
            (point_id, course_id, point, now),
        )
    conn.commit()
    conn.close()
    return list_knowledge_points(course_id, user)


@router.delete("/{course_id}/knowledge-points/{point_id}", response_model=dict)
def delete_knowledge_point(
    course_id: str,
    point_id: str,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    conn = get_connection()
    conn.execute(
        "DELETE FROM knowledge_points WHERE id = ? AND course_id = ?",
        (point_id, course_id),
    )
    conn.commit()
    conn.close()
    return {"data": {"deleted": True}, "meta": {}}


@router.put("/{course_id}/knowledge-points/{point_id}", response_model=dict)
def update_knowledge_point(
    course_id: str,
    point_id: str,
    payload: KnowledgePointCreateRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    conn = get_connection()
    conn.execute(
        "UPDATE knowledge_points SET point = ? WHERE id = ? AND course_id = ?",
        (payload.point, point_id, course_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM knowledge_points WHERE id = ?", (point_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    return {
        "data": KnowledgePointResponse(
            id=row["id"],
            course_id=row["course_id"],
            point=row["point"],
            created_at=row["created_at"],
        ).model_dump(),
        "meta": {},
    }
