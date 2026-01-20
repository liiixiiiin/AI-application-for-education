from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..auth import require_user
from ..schemas import RagEvaluationRequest, RagEvaluationResponse, RagQaRequest, RagQaResponse
from ..services.rag_evaluation import evaluate_rag_response
from ..services.rag_qa import answer_question, stream_answer_events


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


@router.post("/{course_id}/qa/stream")
def course_qa_stream(
    course_id: str,
    payload: RagQaRequest,
    user: dict = Depends(require_user),
) -> StreamingResponse:
    _ = user
    if payload.course_id != course_id:
        raise HTTPException(status_code=400, detail="course_id mismatch")
    event_stream = stream_answer_events(course_id, payload.question, payload.top_k)
    return StreamingResponse(
        event_stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@router.post("/{course_id}/qa/evaluate", response_model=RagEvaluationResponse)
def course_qa_evaluate(
    course_id: str,
    payload: RagEvaluationRequest,
    user: dict = Depends(require_user),
) -> RagEvaluationResponse:
    _ = user
    if payload.course_id != course_id:
        raise HTTPException(status_code=400, detail="course_id mismatch")
    try:
        result = evaluate_rag_response(
            course_id=course_id,
            question=payload.question,
            top_k=payload.top_k,
            answer=payload.answer,
            ground_truth=payload.ground_truth,
            metrics=payload.metrics,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RagEvaluationResponse(**result)
