"""
Audit trail router — read-only event log.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditEvent
from app.schemas import AuditEventOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=list[AuditEventOut])
def list_audit_events(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List audit events, most recent first.
    Read-only — audit events cannot be edited or deleted through the API.
    This is an application-level audit log, not a certified tamper-proof compliance system.
    """
    events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return events


@router.get("/count")
def count_audit_events(db: Session = Depends(get_db)):
    """Get total count of audit events."""
    count = db.query(AuditEvent).count()
    return {"total": count}
