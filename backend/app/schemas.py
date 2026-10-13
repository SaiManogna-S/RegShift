from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ---- Document Schemas ----

class DocumentBase(BaseModel):
    original_name: str
    file_type: str
    file_size: int

class DocumentOut(BaseModel):
    id: int
    filename: str
    original_name: str
    file_type: str
    file_size: int
    status: str
    extraction_error: Optional[str] = None
    upload_timestamp: datetime
    is_demo: bool
    has_text: bool = False

    model_config = {"from_attributes": True}


# ---- Analysis Schemas ----

class AnalysisRunOut(BaseModel):
    id: int
    document_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    is_demo: bool
    llm_used: bool

    model_config = {"from_attributes": True}


class RequirementOut(BaseModel):
    id: int
    analysis_run_id: int
    req_id: str
    summary: str
    source_passage: Optional[str] = None
    page_ref: Optional[str] = None
    jurisdiction: Optional[str] = None
    line_of_business: Optional[str] = None
    effective_date: Optional[str] = None
    change_category: Optional[str] = None
    required_action: Optional[str] = None
    ambiguities: Optional[str] = None
    is_demo: bool

    model_config = {"from_attributes": True}


# ---- Catalogue Schemas ----

class CatalogueItemOut(BaseModel):
    id: int
    item_type: str
    name: str
    jurisdiction: Optional[str] = None
    line_of_business: Optional[str] = None
    description: str
    keywords: Optional[str] = None
    is_demo: bool

    model_config = {"from_attributes": True}


# ---- Impact Schemas ----

class ImpactResultOut(BaseModel):
    id: int
    analysis_run_id: int
    requirement_id: int
    catalogue_item_id: int
    match_reason: str
    confidence: str
    suggested_action: str
    is_demo: bool
    requirement: Optional[RequirementOut] = None
    catalogue_item: Optional[CatalogueItemOut] = None

    model_config = {"from_attributes": True}


# ---- Ticket Schemas ----

class TicketCreate(BaseModel):
    impact_result_id: int
    title: Optional[str] = None
    proposed_action: Optional[str] = None
    priority: Optional[str] = "medium"
    assumptions: Optional[str] = None

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    proposed_action: Optional[str] = None
    priority: Optional[str] = None
    assumptions: Optional[str] = None
    status: Optional[str] = None

class ReviewAction(BaseModel):
    action: str  # approve, reject, request_changes
    comment: Optional[str] = None

class ChangeTicketOut(BaseModel):
    id: int
    ticket_ref: str
    title: str
    requirement_id: int
    impact_result_id: int
    proposed_action: str
    evidence: str
    priority: str
    priority_rationale: str
    effective_date: Optional[str] = None
    assumptions: Optional[str] = None
    status: str
    reviewer_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_demo: bool
    requirement: Optional[RequirementOut] = None
    impact_result: Optional[ImpactResultOut] = None

    model_config = {"from_attributes": True}


# ---- Audit Schemas ----

class AuditEventOut(BaseModel):
    id: int
    event_type: str
    record_id: Optional[int] = None
    record_type: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime
    is_demo_related: bool

    model_config = {"from_attributes": True}


# ---- Overview Stats ----

class OverviewStats(BaseModel):
    total_documents: int
    completed_analyses: int
    pending_reviews: int
    open_tickets: int
    recent_events: List[AuditEventOut]
