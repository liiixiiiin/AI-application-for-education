from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_teacher, require_user
from ..db import get_connection
from ..schemas import CourseCreateRequest, CourseResponse
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
