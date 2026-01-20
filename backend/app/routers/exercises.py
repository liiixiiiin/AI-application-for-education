from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_teacher, require_user
from ..schemas import (
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    ExerciseGradingRequest,
    ExerciseGradingResponse,
    ExerciseBatchSaveRequest,
    ExerciseBatchResponse,
    ExerciseBatchListItem,
    ExerciseBatchUpdateRequest,
)
from ..services.exercises import (
    generate_exercises, 
    grade_exercise, 
    save_exercise_batch, 
    list_exercise_batches, 
    get_exercise_batch, 
    update_exercise_batch, 
    delete_exercise_batch
)


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


@router.post("/{course_id}/exercises/batches", response_model=dict)
def save_course_exercise_batch(
    course_id: str,
    payload: ExerciseBatchSaveRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    batch = save_exercise_batch(
        course_id=course_id,
        exercises=[ex.model_dump() for ex in payload.exercises],
        title=payload.title
    )
    return {"data": batch, "meta": {}}


@router.get("/{course_id}/exercises/batches", response_model=dict)
def get_course_exercise_batches(
    course_id: str,
    user: dict = Depends(require_user),
) -> dict:
    batches = list_exercise_batches(course_id)
    return {"data": batches, "meta": {"count": len(batches)}}


@router.get("/{course_id}/exercises/batches/{batch_id}", response_model=dict)
def get_course_exercise_batch(
    course_id: str,
    batch_id: str,
    user: dict = Depends(require_user),
) -> dict:
    batch = get_exercise_batch(course_id, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"data": batch, "meta": {}}


@router.put("/{course_id}/exercises/batches/{batch_id}", response_model=dict)
def update_course_exercise_batch(
    course_id: str,
    batch_id: str,
    payload: ExerciseBatchUpdateRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    batch = update_exercise_batch(
        course_id=course_id,
        batch_id=batch_id,
        title=payload.title,
        exercises=[ex.model_dump() for ex in payload.exercises] if payload.exercises else None
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"data": batch, "meta": {}}


@router.delete("/{course_id}/exercises/batches/{batch_id}", response_model=dict)
def delete_course_exercise_batch(
    course_id: str,
    batch_id: str,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    success = delete_exercise_batch(course_id, batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"data": {"deleted": True}, "meta": {}}


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
