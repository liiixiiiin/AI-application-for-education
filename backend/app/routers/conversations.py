from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import require_user
from ..schemas import (
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationUpdateRequest,
)
from ..services.memory_store import (
    create_conversation,
    delete_conversation,
    get_conversation_with_messages,
    list_conversations,
    update_conversation_title,
)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse)
def create(payload: ConversationCreateRequest, user: dict = Depends(require_user)):
    conv = create_conversation(user["id"], payload.course_id)
    return ConversationResponse(**conv)


@router.get("", response_model=list[ConversationResponse])
def list_all(
    course_id: str | None = Query(default=None),
    user: dict = Depends(require_user),
):
    convs = list_conversations(user["id"], course_id)
    return [ConversationResponse(**c) for c in convs]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def detail(conversation_id: str, user: dict = Depends(require_user)):
    conv = get_conversation_with_messages(conversation_id)
    if not conv or conv["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetailResponse(**conv)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_title(
    conversation_id: str,
    payload: ConversationUpdateRequest,
    user: dict = Depends(require_user),
):
    conv = update_conversation_title(conversation_id, payload.title)
    if not conv or conv["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(**conv)


@router.delete("/{conversation_id}")
def remove(conversation_id: str, user: dict = Depends(require_user)):
    deleted = delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}
