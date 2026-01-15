from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_user
from ..schemas import (
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    ExerciseGradingRequest,
    ExerciseGradingResponse,
)
from ..services.exercises import generate_exercises, grade_exercise


router = APIRouter(prefix="/api/v1/courses", tags=["exercises"])


@router.post("/{course_id}/exercises/generate", response_model=dict)
def generate_course_exercises(
    course_id: str,
    payload: ExerciseGenerationRequest,
    user: dict = Depends(require_user),
) -> dict:
    _ = user
    if payload.course_id != course_id:
        raise HTTPException(status_code=400, detail="course_id mismatch")
    exercises = generate_exercises(
        course_id=course_id,
        count=payload.count,
        types=payload.types,
        difficulty=payload.difficulty,
        knowledge_scope=payload.knowledge_scope,
    )
    response = ExerciseGenerationResponse(generated=exercises)
    return {"data": response.model_dump(), "meta": {"count": len(exercises)}}


@router.post("/{course_id}/exercises/grade", response_model=dict)
def grade_course_exercise(
    course_id: str,
    payload: ExerciseGradingRequest,
    user: dict = Depends(require_user),
) -> dict:
    _ = user
    if payload.course_id != course_id:
        raise HTTPException(status_code=400, detail="course_id mismatch")
    result = grade_exercise(payload.model_dump())
    response = ExerciseGradingResponse(**result)
    return {"data": response.model_dump(), "meta": {"graded": True}}
