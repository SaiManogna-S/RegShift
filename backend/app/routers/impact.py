"""
Impact analysis router — retrieve impact results and catalogue items.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import ImpactResult, AnalysisRun, InsuranceCatalogueItem
from app.schemas import ImpactResultOut, CatalogueItemOut

router = APIRouter(prefix="/impact", tags=["impact"])


@router.get("/{run_id}", response_model=list[ImpactResultOut])
def get_impact_results(run_id: int, db: Session = Depends(get_db)):
    """Get all impact analysis results for an analysis run."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found.")

    results = (
        db.query(ImpactResult)
        .options(
            joinedload(ImpactResult.requirement),
            joinedload(ImpactResult.catalogue_item),
        )
        .filter(ImpactResult.analysis_run_id == run_id)
        .order_by(
            ImpactResult.confidence.desc(),
            ImpactResult.id.asc(),
        )
        .all()
    )
    return results


@router.get("/result/{impact_id}", response_model=ImpactResultOut)
def get_impact_result(impact_id: int, db: Session = Depends(get_db)):
    """Get a single impact result with full details."""
    result = (
        db.query(ImpactResult)
        .options(
            joinedload(ImpactResult.requirement),
            joinedload(ImpactResult.catalogue_item),
        )
        .filter(ImpactResult.id == impact_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Impact result not found.")
    return result


@router.get("/catalogue/all", response_model=list[CatalogueItemOut])
def get_catalogue(db: Session = Depends(get_db)):
    """Get all insurance catalogue items."""
    items = db.query(InsuranceCatalogueItem).order_by(
        InsuranceCatalogueItem.item_type, InsuranceCatalogueItem.name
    ).all()
    return items
