"""
Overview router — dashboard statistics.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, AnalysisRun, ChangeTicket, AuditEvent
from app.schemas import OverviewStats, AuditEventOut

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("/stats", response_model=OverviewStats)
def get_stats(db: Session = Depends(get_db)):
    """Get dashboard overview statistics backed by real database counts."""
    total_documents = db.query(Document).count()
    completed_analyses = db.query(AnalysisRun).filter(AnalysisRun.status == "completed").count()
    pending_reviews = db.query(ChangeTicket).filter(ChangeTicket.status == "pending_review").count()
    open_tickets = db.query(ChangeTicket).filter(
        ChangeTicket.status.in_(["draft", "pending_review", "changes_requested"])
    ).count()

    recent_events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.timestamp.desc())
        .limit(10)
        .all()
    )

    return OverviewStats(
        total_documents=total_documents,
        completed_analyses=completed_analyses,
        pending_reviews=pending_reviews,
        open_tickets=open_tickets,
        recent_events=[AuditEventOut.model_validate(e) for e in recent_events],
    )
