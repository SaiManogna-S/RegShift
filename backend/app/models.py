from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")  # uploaded, processing, ready, error
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    upload_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    analysis_runs: Mapped[list["AnalysisRun"]] = relationship("AnalysisRun", back_populates="document")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, running, completed, failed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False)

    document: Mapped["Document"] = relationship("Document", back_populates="analysis_runs")
    requirements: Mapped[list["Requirement"]] = relationship("Requirement", back_populates="analysis_run")
    impact_results: Mapped[list["ImpactResult"]] = relationship("ImpactResult", back_populates="analysis_run")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    req_id: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_passage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    line_of_business: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    effective_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    change_category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    required_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ambiguities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="requirements")
    impact_results: Mapped[list["ImpactResult"]] = relationship("ImpactResult", back_populates="requirement")


class InsuranceCatalogueItem(Base):
    __tablename__ = "insurance_catalogue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # product, rule, form
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    line_of_business: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # comma-separated
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)  # catalogue is always synthetic

    impact_results: Mapped[list["ImpactResult"]] = relationship("ImpactResult", back_populates="catalogue_item")


class ImpactResult(Base):
    __tablename__ = "impact_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey("requirements.id"), nullable=False)
    catalogue_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("insurance_catalogue.id"), nullable=False)
    match_reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(50), nullable=False)  # high, medium, low
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="impact_results")
    requirement: Mapped["Requirement"] = relationship("Requirement", back_populates="impact_results")
    catalogue_item: Mapped["InsuranceCatalogueItem"] = relationship("InsuranceCatalogueItem", back_populates="impact_results")
    tickets: Mapped[list["ChangeTicket"]] = relationship("ChangeTicket", back_populates="impact_result")


class ChangeTicket(Base):
    __tablename__ = "change_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey("requirements.id"), nullable=False)
    impact_result_id: Mapped[int] = mapped_column(Integer, ForeignKey("impact_results.id"), nullable=False)
    proposed_action: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)  # critical, high, medium, low
    priority_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    effective_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assumptions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft, pending_review, approved, rejected, changes_requested
    reviewer_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    requirement: Mapped["Requirement"] = relationship("Requirement")
    impact_result: Mapped["ImpactResult"] = relationship("ImpactResult", back_populates="tickets")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    record_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_demo_related: Mapped[bool] = mapped_column(Boolean, default=False)
