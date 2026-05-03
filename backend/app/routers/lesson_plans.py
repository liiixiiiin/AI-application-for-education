from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_teacher, require_user
from ..schemas import LessonOutlineGenerateRequest, LessonOutlineResponse
from ..services.lesson_plans import (
    delete_lesson_outline,
    generate_lesson_outline,
    get_lesson_outline,
    list_lesson_outlines,
    save_lesson_outline,
)


router = APIRouter(prefix="/api/v1/courses", tags=["lesson-plans"])


@router.post("/{course_id}/lesson-outlines/generate", response_model=dict)
def generate_course_lesson_outline(
    course_id: str,
    payload: LessonOutlineGenerateRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    if payload.course_id != course_id:
        raise HTTPException(status_code=400, detail="course_id mismatch")
    outline = generate_lesson_outline(
        course_id=course_id,
        chapter_title=payload.chapter_title,
        duration_minutes=payload.duration_minutes,
        knowledge_scope=payload.knowledge_scope,
        audience_level=payload.audience_level,
        include_practice=payload.include_practice,
    )
    saved_outline = save_lesson_outline(
        course_id=course_id,
        outline=outline,
        created_by=user.get("id"),
    )
    response = LessonOutlineResponse(**saved_outline)
    return {"data": response.model_dump(), "meta": {"generated": True, "saved": True}}


@router.get("/{course_id}/lesson-outlines", response_model=dict)
def get_course_lesson_outlines(
    course_id: str,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    outlines = list_lesson_outlines(course_id)
    return {"data": outlines, "meta": {"count": len(outlines)}}


@router.get("/{course_id}/lesson-outlines/{outline_id}", response_model=dict)
def get_course_lesson_outline(
    course_id: str,
    outline_id: str,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    outline = get_lesson_outline(course_id, outline_id)
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")
    response = LessonOutlineResponse(**outline)
    return {"data": response.model_dump(), "meta": {}}


@router.delete("/{course_id}/lesson-outlines/{outline_id}", response_model=dict)
def delete_course_lesson_outline(
    course_id: str,
    outline_id: str,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    success = delete_lesson_outline(course_id, outline_id)
    if not success:
        raise HTTPException(status_code=404, detail="Outline not found")
    return {"data": {"deleted": True}, "meta": {}}
