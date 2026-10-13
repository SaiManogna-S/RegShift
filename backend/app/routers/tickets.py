"""
Change tickets router — CRUD and review workflow.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import ChangeTicket, ImpactResult, Requirement, AuditEvent
from app.schemas import ChangeTicketOut, TicketCreate, TicketUpdate, ReviewAction

router = APIRouter(prefix="/tickets", tags=["tickets"])
logger = logging.getLogger(__name__)

VALID_STATUSES = {"draft", "pending_review", "approved", "rejected", "changes_requested"}

VALID_TRANSITIONS = {
    "draft": {"pending_review"},
    "pending_review": {"approved", "rejected", "changes_requested"},
    "changes_requested": {"pending_review", "draft"},
    "approved": set(),
    "rejected": set(),
}

PRIORITY_LABELS = {
    "critical": "Critical — immediate regulatory deadline or significant compliance risk",
    "high": "High — near-term effective date or broad product impact",
    "medium": "Medium — moderate scope, action required before effective date",
    "low": "Low — minor or uncertain impact requiring further review",
}


def _get_ticket_or_404(ticket_id: int, db: Session) -> ChangeTicket:
    ticket = (
        db.query(ChangeTicket)
        .options(
            joinedload(ChangeTicket.requirement),
            joinedload(ChangeTicket.impact_result).joinedload(ImpactResult.catalogue_item),
        )
        .filter(ChangeTicket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


def _generate_ticket_ref(db: Session) -> str:
    count = db.query(ChangeTicket).count()
    return f"TKT-{count + 1:04d}"


def _derive_priority(impact: ImpactResult, req: Requirement) -> tuple[str, str]:
    """Derive ticket priority from confidence and change category."""
    high_priority_categories = {"coverage_mandate", "rate_change", "underwriting_restriction"}
    if impact.confidence == "high" and req.change_category in high_priority_categories:
        return "critical", PRIORITY_LABELS["critical"]
    elif impact.confidence == "high":
        return "high", PRIORITY_LABELS["high"]
    elif impact.confidence == "medium":
        return "medium", PRIORITY_LABELS["medium"]
    else:
        return "low", PRIORITY_LABELS["low"]


@router.post("/", response_model=ChangeTicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(body: TicketCreate, db: Session = Depends(get_db)):
    """Create a change ticket from a saved impact result."""
    impact = (
        db.query(ImpactResult)
        .options(
            joinedload(ImpactResult.requirement),
            joinedload(ImpactResult.catalogue_item),
        )
        .filter(ImpactResult.id == body.impact_result_id)
        .first()
    )
    if not impact:
        raise HTTPException(status_code=404, detail="Impact result not found.")

    req = impact.requirement
    catalogue_item = impact.catalogue_item

    # Check no duplicate ticket for this impact
    existing = db.query(ChangeTicket).filter(ChangeTicket.impact_result_id == body.impact_result_id).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A ticket already exists for this impact result: {existing.ticket_ref}",
        )

    priority, priority_rationale = _derive_priority(impact, req)
    if body.priority:
        priority = body.priority

    title = body.title or (
        f"[{catalogue_item.item_type.upper()}] {catalogue_item.name} — "
        f"{req.change_category.replace('_', ' ').title() if req.change_category else 'Regulatory Update'}"
    )

    evidence = (
        f"Regulatory Requirement: {req.req_id} — {req.summary}\n\n"
        f"Source Passage: {req.source_passage or 'N/A'}\n\n"
        f"Jurisdiction: {req.jurisdiction or 'Not specified'}\n"
        f"Line of Business: {req.line_of_business or 'Not specified'}\n"
        f"Effective Date: {req.effective_date or 'Not specified'}\n\n"
        f"Catalogue Item: {catalogue_item.name} ({catalogue_item.item_type})\n"
        f"Match Reason: {impact.match_reason}\n"
        f"Confidence: {impact.confidence.upper()}"
    )

    ticket = ChangeTicket(
        ticket_ref=_generate_ticket_ref(db),
        title=title,
        requirement_id=req.id,
        impact_result_id=impact.id,
        proposed_action=body.proposed_action or req.required_action or "Review and update as required.",
        evidence=evidence,
        priority=priority,
        priority_rationale=priority_rationale,
        effective_date=req.effective_date,
        assumptions=body.assumptions or req.ambiguities,
        status="draft",
        is_demo=impact.is_demo,
    )
    db.add(ticket)
    db.flush()

    db.add(AuditEvent(
        event_type="ticket_created",
        record_id=ticket.id,
        record_type="change_ticket",
        details=f"Ticket {ticket.ticket_ref} created for impact result {impact.id} ('{catalogue_item.name}')",
        is_demo_related=impact.is_demo,
    ))

    db.commit()
    return _get_ticket_or_404(ticket.id, db)


@router.get("/", response_model=list[ChangeTicketOut])
def list_tickets(db: Session = Depends(get_db)):
    """List all change tickets ordered by creation date descending."""
    tickets = (
        db.query(ChangeTicket)
        .options(
            joinedload(ChangeTicket.requirement),
            joinedload(ChangeTicket.impact_result).joinedload(ImpactResult.catalogue_item),
        )
        .order_by(ChangeTicket.created_at.desc())
        .all()
    )
    return tickets


@router.get("/{ticket_id}", response_model=ChangeTicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get a single change ticket with full details."""
    return _get_ticket_or_404(ticket_id, db)


@router.patch("/{ticket_id}", response_model=ChangeTicketOut)
def update_ticket(ticket_id: int, body: TicketUpdate, db: Session = Depends(get_db)):
    """Update a draft change ticket."""
    ticket = _get_ticket_or_404(ticket_id, db)

    if ticket.status not in {"draft", "changes_requested"}:
        raise HTTPException(
            status_code=400,
            detail=f"Only draft or changes_requested tickets can be edited. Current status: {ticket.status}",
        )

    if body.title is not None:
        ticket.title = body.title
    if body.proposed_action is not None:
        ticket.proposed_action = body.proposed_action
    if body.priority is not None:
        if body.priority not in PRIORITY_LABELS:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {body.priority}")
        ticket.priority = body.priority
        ticket.priority_rationale = PRIORITY_LABELS[body.priority]
    if body.assumptions is not None:
        ticket.assumptions = body.assumptions

    ticket.updated_at = datetime.utcnow()

    db.add(AuditEvent(
        event_type="ticket_updated",
        record_id=ticket.id,
        record_type="change_ticket",
        details=f"Ticket {ticket.ticket_ref} updated. Fields changed: {', '.join(k for k, v in body.model_dump(exclude_none=True).items())}",
        is_demo_related=ticket.is_demo,
    ))

    db.commit()
    return _get_ticket_or_404(ticket_id, db)


@router.post("/{ticket_id}/review", response_model=ChangeTicketOut)
def review_ticket(ticket_id: int, body: ReviewAction, db: Session = Depends(get_db)):
    """Record a review decision: approve, reject, or request_changes."""
    ticket = _get_ticket_or_404(ticket_id, db)

    action_to_status = {
        "approve": "approved",
        "reject": "rejected",
        "request_changes": "changes_requested",
    }

    if body.action not in action_to_status:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{body.action}'. Must be one of: approve, reject, request_changes",
        )

    new_status = action_to_status[body.action]
    allowed = VALID_TRANSITIONS.get(ticket.status, set())

    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot transition ticket from '{ticket.status}' to '{new_status}'. "
                f"Allowed transitions from '{ticket.status}': {allowed or 'none — this status is terminal'}"
            ),
        )

    old_status = ticket.status
    ticket.status = new_status
    ticket.reviewer_comment = body.comment
    ticket.updated_at = datetime.utcnow()

    event_map = {
        "approved": "ticket_approved",
        "rejected": "ticket_rejected",
        "changes_requested": "ticket_changes_requested",
    }

    db.add(AuditEvent(
        event_type=event_map[new_status],
        record_id=ticket.id,
        record_type="change_ticket",
        details=(
            f"Ticket {ticket.ticket_ref} {body.action.replace('_', ' ')}. "
            f"Status: {old_status} → {new_status}. "
            f"Comment: {body.comment or 'None'}"
        ),
        is_demo_related=ticket.is_demo,
    ))

    db.commit()
    return _get_ticket_or_404(ticket_id, db)


@router.post("/{ticket_id}/submit", response_model=ChangeTicketOut)
def submit_for_review(ticket_id: int, db: Session = Depends(get_db)):
    """Submit a draft ticket for review."""
    ticket = _get_ticket_or_404(ticket_id, db)

    if ticket.status not in {"draft", "changes_requested"}:
        raise HTTPException(
            status_code=400,
            detail=f"Only draft or changes_requested tickets can be submitted for review. Current status: {ticket.status}",
        )

    old_status = ticket.status
    ticket.status = "pending_review"
    ticket.updated_at = datetime.utcnow()

    db.add(AuditEvent(
        event_type="ticket_submitted_for_review",
        record_id=ticket.id,
        record_type="change_ticket",
        details=f"Ticket {ticket.ticket_ref} submitted for review. Status: {old_status} → pending_review",
        is_demo_related=ticket.is_demo,
    ))

    db.commit()
    return _get_ticket_or_404(ticket_id, db)
