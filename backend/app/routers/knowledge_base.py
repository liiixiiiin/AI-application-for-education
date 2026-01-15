from fastapi import APIRouter, Depends

from ..auth import require_teacher, require_user
from ..schemas import (
    DocumentMetadata,
    DocumentSearchRequest,
    DocumentUploadRequest,
)
from ..services.knowledge_base import list_documents, search_documents, store_documents


router = APIRouter(prefix="/api/v1/courses", tags=["knowledge-base"])


@router.get("/{course_id}/documents", response_model=dict)
def get_documents(course_id: str, user: dict = Depends(require_user)) -> dict:
    documents = [DocumentMetadata(**doc).model_dump() for doc in list_documents(course_id)]
    return {"data": documents, "meta": {"count": len(documents)}}


@router.post("/{course_id}/documents", response_model=dict)
def upload_documents(
    course_id: str,
    payload: DocumentUploadRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    documents = store_documents(
        course_id,
        [doc.model_dump() for doc in payload.documents],
    )
    response = [DocumentMetadata(**doc).model_dump() for doc in documents]
    return {"data": response, "meta": {"count": len(response)}}


@router.post("/{course_id}/documents/search", response_model=dict)
def search_course_documents(
    course_id: str,
    payload: DocumentSearchRequest,
    user: dict = Depends(require_user),
) -> dict:
    results = search_documents(
        course_id,
        payload.query,
        payload.top_k,
        payload.filters,
    )
    return {
        "data": {"query": payload.query, "results": results},
        "meta": {"count": len(results)},
    }
