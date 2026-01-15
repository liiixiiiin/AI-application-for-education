from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_user
from ..schemas import RagQaRequest, RagQaResponse
from ..services.rag_qa import answer_question


router = APIRouter(prefix="/api/v1/courses", tags=["rag-qa"])


@router.post("/{course_id}/qa", response_model=RagQaResponse)
def course_qa(
    course_id: str,
    payload: RagQaRequest,
    user: dict = Depends(require_user),
) -> RagQaResponse:
    _ = user
    if payload.course_id != course_id:
        raise HTTPException(status_code=400, detail="course_id mismatch")
    result = answer_question(course_id, payload.question, payload.top_k)
    return RagQaResponse(**result)
