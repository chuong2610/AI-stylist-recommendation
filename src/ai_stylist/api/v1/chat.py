import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai_stylist.db.postgres import get_db
from ai_stylist.schemas.chat import (
    SessionCreate,
    SessionResponse,
    MessageCreate,
    MessageResponse,
    ChatResponse,
)
from ai_stylist.services.chat.session_service import SessionService
from ai_stylist.services.chat.agent_service import AgentService

router = APIRouter(prefix="/sessions", tags=["chat"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    svc = SessionService(db)
    return await svc.create_session(user_id=body.user_id, title=body.title)


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    user_id: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    svc = SessionService(db)
    return await svc.list_sessions(user_id, limit=limit, offset=offset)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = SessionService(db)
    session = await svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = SessionService(db)
    if not await svc.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def list_messages(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = SessionService(db)
    if not await svc.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return await svc.list_messages(session_id)


@router.post("/{session_id}/messages", response_model=ChatResponse)
async def send_message(session_id: uuid.UUID, body: MessageCreate, db: AsyncSession = Depends(get_db)):
    svc = SessionService(db)
    session = await svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = AgentService(db)
    result = await agent.handle(
        session_id=session_id,
        user_message=body.content,
        user_id=session.user_id,
    )

    # Lấy assistant message vừa được lưu
    history = await svc.get_history(session_id, n=2)
    assistant_msg = next((m for m in reversed(history) if m.role == "assistant"), None)
    if not assistant_msg:
        raise HTTPException(status_code=500, detail="Failed to save assistant message")

    return ChatResponse(
        message=MessageResponse.model_validate(assistant_msg),
        outfit_plan=result.get("outfit_plan"),
    )
