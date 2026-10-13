"""
Analysis router — start requirement extraction, retrieve results.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, AnalysisRun, Requirement, ImpactResult, AuditEvent
from app.schemas import AnalysisRunOut, RequirementOut
from app.services import llm as llm_service
from app.services.matching import run_impact_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)


@router.post("/start/{document_id}", response_model=AnalysisRunOut)
async def start_analysis(document_id: int, db: Session = Depends(get_db)):
    """
    Start AI requirement extraction for an uploaded document.
    Runs synchronously and returns the completed analysis run.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Document is not ready for analysis. Current status: {doc.status}. "
                   f"{'Error: ' + doc.extraction_error if doc.extraction_error else ''}",
        )

    if not doc.extracted_text or not doc.extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document has no extracted text. Cannot run analysis.",
        )

    # Create analysis run
    run = AnalysisRun(
        document_id=document_id,
        status="running",
        started_at=datetime.utcnow(),
        is_demo=doc.is_demo,
    )
    db.add(run)
    db.flush()

    db.add(AuditEvent(
        event_type="analysis_started",
        record_id=run.id,
        record_type="analysis_run",
        details=f"Started analysis for document '{doc.original_name}' (ID: {document_id})",
        is_demo_related=doc.is_demo,
    ))
    db.commit()

    # Run LLM extraction
    try:
        result = await llm_service.extract_requirements(doc.extracted_text)
    except Exception as e:
        logger.exception("Unexpected error in LLM extraction")
        run.status = "failed"
        run.completed_at = datetime.utcnow()
        run.error_message = f"Unexpected error: {str(e)}"
        db.add(AuditEvent(
            event_type="analysis_failed",
            record_id=run.id,
            record_type="analysis_run",
            details=run.error_message,
            is_demo_related=doc.is_demo,
        ))
        db.commit()
        raise HTTPException(status_code=500, detail=run.error_message)

    if "error" in result and not result.get("requirements"):
        run.status = "failed"
        run.completed_at = datetime.utcnow()
        run.error_message = result.get("error", "Unknown extraction error")
        db.add(AuditEvent(
            event_type="analysis_failed",
            record_id=run.id,
            record_type="analysis_run",
            details=run.error_message,
            is_demo_related=doc.is_demo,
        ))
        db.commit()
        db.refresh(run)
        return run

    # Save requirements
    run.llm_used = result.get("llm_used", False)
    req_objects = []
    for req_data in result.get("requirements", []):
        req = Requirement(
            analysis_run_id=run.id,
            req_id=req_data.get("req_id", f"REQ-{len(req_objects)+1:03d}"),
            summary=req_data.get("summary", ""),
            source_passage=req_data.get("source_passage"),
            page_ref=req_data.get("page_ref"),
            jurisdiction=req_data.get("jurisdiction"),
            line_of_business=req_data.get("line_of_business"),
            effective_date=req_data.get("effective_date"),
            change_category=req_data.get("change_category"),
            required_action=req_data.get("required_action"),
            ambiguities=req_data.get("ambiguities"),
            is_demo=doc.is_demo,
        )
        db.add(req)
        req_objects.append(req)

    db.flush()

    # Run impact matching
    impact_matches = run_impact_analysis(db, run.id, req_objects)
    for match in impact_matches:
        impact = ImpactResult(
            analysis_run_id=run.id,
            requirement_id=match["requirement_id"],
            catalogue_item_id=match["catalogue_item_id"],
            match_reason=match["match_reason"],
            confidence=match["confidence"],
            suggested_action=match["suggested_action"],
            is_demo=doc.is_demo,
        )
        db.add(impact)

    run.status = "completed"
    run.completed_at = datetime.utcnow()

    notes = result.get("extraction_notes", "")
    is_demo_extraction = result.get("is_demo_extraction", False)

    db.add(AuditEvent(
        event_type="analysis_completed",
        record_id=run.id,
        record_type="analysis_run",
        details=(
            f"Analysis completed. {len(req_objects)} requirements extracted. "
            f"LLM used: {run.llm_used}. "
            f"{'[DEMO MODE - no real AI analysis] ' if is_demo_extraction else ''}"
            f"{notes[:200] if notes else ''}"
        ),
        is_demo_related=doc.is_demo or is_demo_extraction,
    ))

    db.commit()
    db.refresh(run)
    return run


@router.get("/{run_id}", response_model=AnalysisRunOut)
def get_analysis_run(run_id: int, db: Session = Depends(get_db)):
    """Get analysis run status and metadata."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    return run


@router.get("/{run_id}/requirements", response_model=list[RequirementOut])
def get_requirements(run_id: int, db: Session = Depends(get_db)):
    """Get all extracted requirements for an analysis run."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    return run.requirements


@router.get("/document/{document_id}/runs", response_model=list[AnalysisRunOut])
def get_runs_for_document(document_id: int, db: Session = Depends(get_db)):
    """Get all analysis runs for a specific document."""
    runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.document_id == document_id)
        .order_by(AnalysisRun.started_at.desc())
        .all()
    )
    return runs
