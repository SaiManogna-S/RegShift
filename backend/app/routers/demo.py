"""
Demo data router — load and reset demo scenario.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document
from app.services.demo_seeder import seed_catalogue, seed_demo_scenario, reset_demo_data

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/load")
def load_demo(db: Session = Depends(get_db)):
    """
    Load the demo regulatory scenario.
    Clears existing demo data first, then seeds catalogue and scenario.
    Audit history is preserved.
    """
    # Reset existing demo first
    reset_demo_data(db)

    # Re-seed catalogue (always done on load)
    catalogue_count = seed_catalogue(db)

    # Seed demo scenario
    result = seed_demo_scenario(db)

    return {
        "status": "success",
        "message": "Demo scenario loaded successfully. This data is synthetic and fictional.",
        "catalogue_items_loaded": catalogue_count,
        **result,
    }


@router.post("/reset")
def reset_demo(db: Session = Depends(get_db)):
    """
    Remove all demo records.
    Audit history is preserved (including demo events).
    """
    result = reset_demo_data(db)
    return {
        "status": "success",
        "message": "Demo data cleared. Audit history preserved.",
        **result,
    }


@router.get("/status")
def demo_status(db: Session = Depends(get_db)):
    """Check whether demo data is currently loaded."""
    demo_doc_count = db.query(Document).filter(Document.is_demo == True).count()
    return {
        "demo_loaded": demo_doc_count > 0,
        "demo_documents": demo_doc_count,
    }
