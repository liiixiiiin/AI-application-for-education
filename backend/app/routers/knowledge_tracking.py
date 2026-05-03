from fastapi import APIRouter, Depends, Query

from ..auth import require_user
from ..schemas import (
    ExerciseGenerationResponse,
    KnowledgeStateResponse,
    RecommendedExercisesRequest,
)
from ..services.knowledge_tracking import (
    generate_recommended_exercises,
    get_exercise_attempts,
    get_knowledge_state,
)

router = APIRouter(prefix="/api/v1", tags=["knowledge-tracking"])


@router.get("/knowledge-state", response_model=dict)
def api_get_knowledge_state(
    course_id: str = Query(..., min_length=1),
    user: dict = Depends(require_user),
) -> dict:
    state = get_knowledge_state(user["id"], course_id)
    response = KnowledgeStateResponse(**state)
    return {"data": response.model_dump(), "meta": {"count": len(response.items)}}


@router.post("/recommended-exercises", response_model=dict)
def api_recommended_exercises(
    payload: RecommendedExercisesRequest,
    user: dict = Depends(require_user),
) -> dict:
    exercises = generate_recommended_exercises(
        student_id=user["id"],
        course_id=payload.course_id,
        count=payload.count,
        difficulty=payload.difficulty,
    )
    response = ExerciseGenerationResponse(generated=exercises)
    return {"data": response.model_dump(), "meta": {"count": len(exercises)}}


@router.get("/exercise-attempts", response_model=dict)
def api_get_exercise_attempts(
    course_id: str = Query(..., min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(require_user),
) -> dict:
    attempts = get_exercise_attempts(user["id"], course_id, limit=limit)
    return {"data": attempts, "meta": {"count": len(attempts)}}
