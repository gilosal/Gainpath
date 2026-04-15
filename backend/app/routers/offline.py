from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.session import OfflineQueue, SessionLog, SetLog, BodyFeedback
from ..schemas.session import OfflineQueueItemCreate, OfflineQueueItemRead

router = APIRouter(prefix="/offline", tags=["offline"])


@router.post("/queue", response_model=OfflineQueueItemRead, status_code=201)
def enqueue_offline_action(payload: OfflineQueueItemCreate, db: Session = Depends(get_db)):
    item = OfflineQueue(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/queue", response_model=list[OfflineQueueItemRead])
def list_pending(db: Session = Depends(get_db)):
    return (
        db.query(OfflineQueue)
        .filter(OfflineQueue.sync_status.in_(["pending", "failed"]))
        .order_by(OfflineQueue.created_at)
        .all()
    )


@router.post("/sync")
def sync_offline_queue(db: Session = Depends(get_db)):
    """
    Process all pending offline queue items in order.
    Returns a summary of synced vs failed items.
    """
    pending = (
        db.query(OfflineQueue)
        .filter(OfflineQueue.sync_status.in_(["pending", "failed"]))
        .order_by(OfflineQueue.created_at)
        .all()
    )

    synced, failed = 0, 0
    for item in pending:
        item.sync_status = "syncing"
        db.commit()
        try:
            _apply_action(item, db)
            item.sync_status = "synced"
            item.synced_at = datetime.utcnow()
            synced += 1
        except Exception as exc:
            item.sync_status = "failed"
            item.error_message = str(exc)
            item.retry_count += 1
            failed += 1
        db.commit()

    return {"synced": synced, "failed": failed, "total": len(pending)}


def _apply_action(item: OfflineQueue, db: Session) -> None:
    action = item.action_type
    payload = item.payload

    if action == "create_set_log":
        session_id = payload.get("session_log_id")
        if not session_id:
            raise ValueError("session_log_id required for create_set_log")
        set_log = SetLog(
            session_log_id=UUID(session_id),
            **{k: v for k, v in payload.items() if k != "session_log_id"},
        )
        db.add(set_log)

    elif action == "complete_session":
        session_id = payload.get("session_log_id")
        log = db.query(SessionLog).filter(SessionLog.id == UUID(session_id)).first()
        if not log:
            raise ValueError(f"SessionLog {session_id} not found")
        for k, v in payload.items():
            if k != "session_log_id" and hasattr(log, k):
                setattr(log, k, v)

    elif action == "add_body_feedback":
        session_id = payload.get("session_log_id")
        fb = BodyFeedback(
            session_log_id=UUID(session_id),
            **{k: v for k, v in payload.items() if k != "session_log_id"},
        )
        db.add(fb)

    else:
        raise ValueError(f"Unknown action type: {action}")
