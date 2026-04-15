from __future__ import annotations

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.coaching import CoachingMessage, ChatMessage
from ..services import coaching_engine

router = APIRouter(prefix="/coaching", tags=["coaching"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CoachingMessageRead(BaseModel):
    id: str
    created_at: str
    message_type: str
    content: str
    displayed: bool
    dismissed: bool

    model_config = {"from_attributes": True}


class ChatMessageRead(BaseModel):
    id: str
    created_at: str
    role: str
    content: str

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/messages", response_model=list[CoachingMessageRead])
def list_messages(
    message_type: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(CoachingMessage).filter(CoachingMessage.dismissed == False)
    if message_type:
        q = q.filter(CoachingMessage.message_type == message_type)
    rows = q.order_by(CoachingMessage.created_at.desc()).limit(limit).all()
    return [
        CoachingMessageRead(
            id=str(m.id),
            created_at=str(m.created_at),
            message_type=m.message_type,
            content=m.content,
            displayed=m.displayed,
            dismissed=m.dismissed,
        )
        for m in rows
    ]


@router.get("/messages/latest", response_model=Optional[CoachingMessageRead])
def latest_message(
    message_type: str = Query(...),
    db: Session = Depends(get_db),
):
    msg = (
        db.query(CoachingMessage)
        .filter(
            CoachingMessage.message_type == message_type,
            CoachingMessage.dismissed == False,
        )
        .order_by(CoachingMessage.created_at.desc())
        .first()
    )
    if not msg:
        return None
    return CoachingMessageRead(
        id=str(msg.id),
        created_at=str(msg.created_at),
        message_type=msg.message_type,
        content=msg.content,
        displayed=msg.displayed,
        dismissed=msg.dismissed,
    )


@router.post("/messages/{message_id}/dismiss", status_code=204)
def dismiss_message(message_id: UUID, db: Session = Depends(get_db)):
    msg = db.query(CoachingMessage).filter(CoachingMessage.id == message_id).first()
    if not msg:
        raise HTTPException(404, "Message not found")
    msg.dismissed = True
    db.commit()


@router.post("/messages/{message_id}/mark-displayed", status_code=204)
def mark_displayed(message_id: UUID, db: Session = Depends(get_db)):
    msg = db.query(CoachingMessage).filter(CoachingMessage.id == message_id).first()
    if not msg:
        raise HTTPException(404, "Message not found")
    msg.displayed = True
    db.commit()


@router.post("/generate/daily", status_code=202)
def trigger_daily_motivation(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger daily motivation generation (normally called by scheduler)."""
    background_tasks.add_task(coaching_engine.generate_daily_motivation, db)
    return {"status": "queued"}


@router.post("/generate/weekly-summary", status_code=202)
def trigger_weekly_summary(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    background_tasks.add_task(coaching_engine.generate_weekly_summary, db)
    return {"status": "queued"}


@router.post("/generate/post-workout/{session_id}", status_code=202)
def trigger_post_workout(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    background_tasks.add_task(coaching_engine.generate_post_workout_feedback, db, session_id, 0)
    return {"status": "queued"}


@router.get("/chat", response_model=list[ChatMessageRead])
def get_chat_history(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ChatMessage)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()
    return [
        ChatMessageRead(
            id=str(m.id),
            created_at=str(m.created_at),
            role=m.role,
            content=m.content,
        )
        for m in rows
    ]


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
):
    response_text = await coaching_engine.chat(db, payload.message)

    # Fetch the two most recently stored messages
    recent = (
        db.query(ChatMessage)
        .order_by(ChatMessage.created_at.desc())
        .limit(2)
        .all()
    )
    recent.reverse()
    user_msg, assistant_msg = recent[0], recent[1]

    return ChatResponse(
        user_message=ChatMessageRead(
            id=str(user_msg.id),
            created_at=str(user_msg.created_at),
            role=user_msg.role,
            content=user_msg.content,
        ),
        assistant_message=ChatMessageRead(
            id=str(assistant_msg.id),
            created_at=str(assistant_msg.created_at),
            role=assistant_msg.role,
            content=assistant_msg.content,
        ),
    )
