"""Agent 路由（agent-spec §9）。"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..agents import run_agent, stream_agent_events
from ..auth import require_user
from ..schemas import AgentRunRequest, AgentRunResponse


router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/run", response_model=AgentRunResponse)
def agent_run(
    payload: AgentRunRequest,
    user: dict = Depends(require_user),
) -> AgentRunResponse:
    result = run_agent(
        user_input=payload.user_input,
        course_id=payload.course_id,
        user_id=user.get("id"),
        conversation_id=payload.conversation_id,
        extra_inputs=payload.extra_inputs,
        time_budget_seconds=payload.time_budget_seconds,
    )
    return AgentRunResponse(**result)


@router.post("/run/stream")
def agent_run_stream(
    payload: AgentRunRequest,
    user: dict = Depends(require_user),
) -> StreamingResponse:
    event_stream = stream_agent_events(
        user_input=payload.user_input,
        course_id=payload.course_id,
        user_id=user.get("id"),
        conversation_id=payload.conversation_id,
        extra_inputs=payload.extra_inputs,
        time_budget_seconds=payload.time_budget_seconds,
    )
    return StreamingResponse(
        event_stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
