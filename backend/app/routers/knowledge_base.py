from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..auth import require_teacher, require_user
from ..schemas import (
    DocumentChunk,
    DocumentMetadata,
    DocumentSearchRequest,
    DocumentUploadRequest,
    DocumentUpdateRequest,
    DocumentWebUploadRequest,
)
from ..services.knowledge_base import (
    extract_upload_payload,
    extract_web_payload,
    delete_document,
    generate_knowledge_points,
    list_document_chunks,
    list_documents,
    search_documents,
    store_documents,
    store_uploaded_documents,
    update_document,
)


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
        use_llm_chunking=payload.use_llm_chunking,
    )
    response = [DocumentMetadata(**doc).model_dump() for doc in documents]
    return {"data": response, "meta": {"count": len(response)}}


@router.post("/{course_id}/documents/upload", response_model=dict)
def upload_document_files(
    course_id: str,
    files: list[UploadFile] = File(...),
    use_llm_chunking: bool | None = None,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    uploads = []
    for uploaded in files:
        payload = extract_upload_payload(uploaded.filename or "unknown", uploaded.file.read())
        uploads.append(payload)
    documents = store_uploaded_documents(course_id, uploads, use_llm_chunking=use_llm_chunking)
    response = [DocumentMetadata(**doc).model_dump() for doc in documents]
    return {"data": response, "meta": {"count": len(response)}}


@router.post("/{course_id}/documents/web", response_model=dict)
def upload_document_web(
    course_id: str,
    payload: DocumentWebUploadRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    urls = [item.strip() for item in payload.urls if item and item.strip()]
    if not urls:
        raise HTTPException(status_code=400, detail="url is required")
    uploads = []
    for url in urls:
        try:
            uploads.append(extract_web_payload(url, payload.parse_classes))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="failed to load web content") from exc
    documents = store_uploaded_documents(course_id, uploads, use_llm_chunking=payload.use_llm_chunking)
    response = [DocumentMetadata(**doc).model_dump() for doc in documents]
    return {"data": response, "meta": {"count": len(response)}}


@router.delete("/{course_id}/documents/{doc_id}", response_model=dict)
def delete_course_document(
    course_id: str,
    doc_id: str,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    deleted = delete_document(course_id, doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="document not found")
    return {"data": {"deleted": True, "doc_id": doc_id}, "meta": {}}


@router.get("/{course_id}/documents/{doc_id}/chunks", response_model=dict)
def get_document_chunks(
    course_id: str,
    doc_id: str,
    user: dict = Depends(require_user),
) -> dict:
    chunks = [DocumentChunk(**chunk).model_dump() for chunk in list_document_chunks(course_id, doc_id)]
    return {"data": chunks, "meta": {"count": len(chunks)}}


@router.put("/{course_id}/documents/{doc_id}", response_model=dict)
def update_course_document(
    course_id: str,
    doc_id: str,
    payload: DocumentUpdateRequest,
    user: dict = Depends(require_user),
) -> dict:
    require_teacher(user)
    if payload.name is None and payload.doc_type is None and payload.content is None:
        raise HTTPException(status_code=400, detail="update payload is empty")
    updated = update_document(
        course_id,
        doc_id,
        name=payload.name,
        doc_type=payload.doc_type,
        content=payload.content,
        use_llm_chunking=payload.use_llm_chunking,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="document not found")
    response = DocumentMetadata(**updated).model_dump()
    return {"data": response, "meta": {}}


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


@router.get("/{course_id}/knowledge-points/generate", response_model=dict)
def generate_course_knowledge_points(
    course_id: str,
    limit: int = 12,
    use_llm: bool | None = None,
    user: dict = Depends(require_user),
) -> dict:
    points = generate_knowledge_points(course_id, limit=limit, use_llm=use_llm)
    return {"data": {"points": points}, "meta": {"count": len(points)}}
