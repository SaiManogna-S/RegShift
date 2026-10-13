"""
Demo data seeder — loads a synthetic regulatory scenario with fictional data.
Clearly labelled as NOT real regulations or real carrier systems.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import (
    Document, AnalysisRun, Requirement,
    InsuranceCatalogueItem, ImpactResult, ChangeTicket, AuditEvent
)

logger = logging.getLogger(__name__)

DEMO_BULLETIN_TEXT = """
CALIFORNIA DEPARTMENT OF INSURANCE
Bulletin 2025-HO-003 (SYNTHETIC DEMO — NOT A REAL REGULATION)

Date: October 1, 2025
Subject: Wildfire Risk Disclosure and Rating Requirements for Homeowner Insurers

I. PURPOSE

This bulletin establishes requirements for admitted homeowner insurers writing policies
in California wildfire risk zones. These requirements take effect January 1, 2026.

NOTE: This document is entirely fictional and is provided solely for demonstration
purposes within the RegShift application.

II. BACKGROUND

The California Department of Insurance has determined that policyholders in wildfire
risk zones require additional disclosure of coverage limitations and surcharge basis.

III. REQUIREMENTS

Section 1 — Disclosure Requirements

1.1 All admitted homeowner insurers writing HO-3 or HO-5 policies in Tier 1 or Tier 2
wildfire risk zones as defined by CDI mapping must include a standardized wildfire
coverage disclosure statement in each policy at issuance and renewal.

1.2 The disclosure must clearly state: (a) whether wildfire coverage is included or
excluded; (b) the applicable deductible; (c) the basis for any wildfire risk surcharge.

Section 2 — Rating Requirements

2.1 No insurer may apply a wildfire risk surcharge exceeding fifteen percent (15%) of
the otherwise applicable base premium for homeowner policies.

2.2 Insurers must file any updates to their wildfire rating plans with the Department
no later than 120 days before the effective date of the change.

Section 3 — Reporting Requirements

3.1 Each admitted homeowner insurer shall submit an annual wildfire claims experience
report to the Department by March 31 of each calendar year, beginning March 31, 2026.

3.2 The report shall include: total wildfire claims count, total incurred losses,
average claim severity, and geographic distribution by county.

Section 4 — Underwriting Restrictions

4.1 Insurers may not non-renew a policy solely on the basis of wildfire risk zone
classification unless the insurer has filed a supporting actuarial justification.

4.2 Any non-renewal based on wildfire risk must be accompanied by a written notice
to the policyholder at least 75 days before expiration.

IV. EFFECTIVE DATE

These requirements are effective January 1, 2026, except Section 3.1 reporting
requirements which take effect March 31, 2026.

V. QUESTIONS

Address questions to the CDI Property & Casualty Division.

[END OF SYNTHETIC DEMO BULLETIN]
"""


DEMO_REQUIREMENTS = [
    {
        "req_id": "DEMO-REQ-001",
        "summary": "Wildfire coverage disclosure required in all HO-3/HO-5 policies in Tier 1/2 risk zones",
        "source_passage": "All admitted homeowner insurers writing HO-3 or HO-5 policies in Tier 1 or Tier 2 wildfire risk zones must include a standardized wildfire coverage disclosure statement in each policy at issuance and renewal.",
        "page_ref": "Section 1.1",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "effective_date": "2026-01-01",
        "change_category": "disclosure_requirement",
        "required_action": "Add standardized wildfire disclosure to HO-3 and HO-5 forms. File updated forms with CDI before October 3, 2025 (120 days prior).",
        "ambiguities": "CDI mapping definition of 'Tier 1' and 'Tier 2' zones not reproduced in this bulletin. Bulletin does not specify the exact disclosure language — reference to CDI template required.",
    },
    {
        "req_id": "DEMO-REQ-002",
        "summary": "Wildfire risk surcharge capped at 15% of base premium",
        "source_passage": "No insurer may apply a wildfire risk surcharge exceeding fifteen percent (15%) of the otherwise applicable base premium for homeowner policies.",
        "page_ref": "Section 2.1",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "effective_date": "2026-01-01",
        "change_category": "rate_change",
        "required_action": "Review wildfire surcharge factors in rating algorithm. Cap wildfire surcharges at 15% of base premium. Re-file rate manual with CDI if current surcharges exceed this cap.",
        "ambiguities": "Unclear whether '15% cap' applies to each individual wildfire endorsement or the aggregate of all wildfire-related surcharges. CDI guidance recommended.",
    },
    {
        "req_id": "DEMO-REQ-003",
        "summary": "Annual wildfire claims experience report due March 31 each year",
        "source_passage": "Each admitted homeowner insurer shall submit an annual wildfire claims experience report to the Department by March 31 of each calendar year, beginning March 31, 2026.",
        "page_ref": "Section 3.1",
        "jurisdiction": "California",
        "line_of_business": None,
        "effective_date": "2026-03-31",
        "change_category": "reporting_requirement",
        "required_action": "Implement annual wildfire claims data reporting process. Compile claims count, incurred losses, average severity, and county distribution. Submit to CDI by March 31, 2026.",
        "ambiguities": "Report submission format and CDI portal not specified in this bulletin.",
    },
    {
        "req_id": "DEMO-REQ-004",
        "summary": "Non-renewal for wildfire risk zone requires actuarial justification and 75-day notice",
        "source_passage": "Insurers may not non-renew a policy solely on the basis of wildfire risk zone classification unless the insurer has filed a supporting actuarial justification. Any non-renewal based on wildfire risk must be accompanied by a written notice to the policyholder at least 75 days before expiration.",
        "page_ref": "Section 4.1-4.2",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "effective_date": "2026-01-01",
        "change_category": "underwriting_restriction",
        "required_action": "Update non-renewal procedures and notice templates. Ensure actuarial justification is on file before processing wildfire-based non-renewals. Extend notice period to 75 days.",
        "ambiguities": "Actuarial justification filing process not specified. Unclear whether existing non-renewals in progress are grandfathered.",
    },
]


DEMO_CATALOGUE_ITEMS = [
    # Products
    {
        "item_type": "product",
        "name": "HO-3 Special Form Homeowners",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Standard open-perils homeowner insurance product for owner-occupied residences. Covers structure and personal property. Written in California under admitted status.",
        "keywords": "homeowner,HO-3,dwelling,wildfire,California,property,residence,structure",
    },
    {
        "item_type": "product",
        "name": "HO-5 Comprehensive Homeowners",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Open-perils homeowner product for high-value residences in California. Provides broader coverage than HO-3 with higher replacement cost limits.",
        "keywords": "homeowner,HO-5,dwelling,wildfire,California,high-value,comprehensive",
    },
    {
        "item_type": "product",
        "name": "Commercial Property Package",
        "jurisdiction": "All States",
        "line_of_business": "Commercial Property",
        "description": "Commercial property coverage for business owners, including building and business personal property. Does not cover residential wildfire risk.",
        "keywords": "commercial,property,business,building,contents",
    },
    {
        "item_type": "product",
        "name": "Personal Auto Package",
        "jurisdiction": "All States",
        "line_of_business": "Personal Auto",
        "description": "Personal automobile liability and physical damage coverage. No wildfire or property components.",
        "keywords": "auto,vehicle,liability,collision,comprehensive",
    },
    # Underwriting Rules
    {
        "item_type": "rule",
        "name": "CA-HO-RATE-007: Wildfire Zone Surcharge Schedule",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Underwriting rule defining wildfire risk zone classifications (Tier 1, 2, 3) and applicable premium surcharges. Current surcharge schedule applies up to 22% for Tier 1 zones.",
        "keywords": "wildfire,surcharge,rate,premium,California,homeowner,tier,zone,pricing,rating",
    },
    {
        "item_type": "rule",
        "name": "CA-HO-UW-012: Non-Renewal Eligibility for High-Risk Properties",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Underwriting guideline specifying conditions under which policies may be non-renewed, including property location in wildfire risk zones. Current notice period is 60 days.",
        "keywords": "non-renewal,eligibility,wildfire,California,homeowner,notice,cancellation,underwriting",
    },
    {
        "item_type": "rule",
        "name": "CA-HO-UW-003: New Business Underwriting Eligibility",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Defines eligibility criteria for new homeowner business in California, including construction type, age, and proximity to brush.",
        "keywords": "eligibility,California,homeowner,new business,brush,construction,underwriting",
    },
    {
        "item_type": "rule",
        "name": "NATL-AUTO-RATE-001: Base Rate Filing",
        "jurisdiction": "All States",
        "line_of_business": "Personal Auto",
        "description": "National base rate schedule for personal automobile insurance. Not related to property or wildfire.",
        "keywords": "auto,rate,premium,base,vehicle",
    },
    # Policy Forms
    {
        "item_type": "form",
        "name": "CA-HO3-001: California HO-3 Policy Form",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Filed California HO-3 policy form. Does not currently contain wildfire risk disclosure language. Last filed: 2022.",
        "keywords": "HO-3,form,policy,California,homeowner,disclosure,wildfire,endorsement",
    },
    {
        "item_type": "form",
        "name": "CA-HO5-001: California HO-5 Policy Form",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Filed California HO-5 comprehensive homeowner policy form. Last filed: 2023. Does not include wildfire-specific disclosure.",
        "keywords": "HO-5,form,policy,California,homeowner,disclosure,wildfire",
    },
    {
        "item_type": "form",
        "name": "CA-HO-END-WF01: Wildfire Coverage Endorsement",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Optional wildfire coverage endorsement for California homeowner policies. Modifies base form to add or clarify wildfire perils. Filed 2021.",
        "keywords": "wildfire,endorsement,California,homeowner,coverage,form,disclosure",
    },
    {
        "item_type": "form",
        "name": "NATL-AUTO-001: Personal Auto Policy Form",
        "jurisdiction": "All States",
        "line_of_business": "Personal Auto",
        "description": "Standard personal auto policy form used nationally. Not related to homeowner or wildfire.",
        "keywords": "auto,vehicle,liability,collision,form",
    },
    {
        "item_type": "form",
        "name": "CA-HO-NOTICE-001: California Non-Renewal Notice Template",
        "jurisdiction": "California",
        "line_of_business": "Homeowners",
        "description": "Standard non-renewal notice letter template for California homeowner policies. Currently specifies 60-day notice period.",
        "keywords": "non-renewal,notice,California,homeowner,cancellation,letter,template",
    },
]


def seed_catalogue(db: Session) -> int:
    """Seed the insurance catalogue with demo items. Returns count of items added."""
    # Clear existing catalogue items first
    db.query(InsuranceCatalogueItem).delete()

    items = []
    for item_data in DEMO_CATALOGUE_ITEMS:
        item = InsuranceCatalogueItem(**item_data, is_demo=True)
        db.add(item)
        items.append(item)

    db.commit()
    return len(items)


def seed_demo_scenario(db: Session) -> dict:
    """
    Seed a complete demo scenario: document, analysis run, requirements, impacts.
    Returns dict with created record IDs.
    """
    # Create demo document
    demo_doc = Document(
        filename="demo_bulletin_2025_ho_003.txt",
        original_name="[DEMO] CDI Bulletin 2025-HO-003 (Synthetic)",
        file_type="text/plain",
        file_size=len(DEMO_BULLETIN_TEXT.encode()),
        status="ready",
        extracted_text=DEMO_BULLETIN_TEXT,
        is_demo=True,
    )
    db.add(demo_doc)
    db.flush()

    # Save the demo bulletin text to disk
    import os
    from app.config import settings
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    bulletin_path = os.path.join(upload_dir, "demo_bulletin_2025_ho_003.txt")
    with open(bulletin_path, "w", encoding="utf-8") as f:
        f.write(DEMO_BULLETIN_TEXT)

    # Create analysis run
    demo_run = AnalysisRun(
        document_id=demo_doc.id,
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        is_demo=True,
        llm_used=False,
    )
    db.add(demo_run)
    db.flush()

    # Create requirements
    req_objs = []
    for req_data in DEMO_REQUIREMENTS:
        req = Requirement(
            analysis_run_id=demo_run.id,
            is_demo=True,
            **req_data,
        )
        db.add(req)
        req_objs.append(req)
    db.flush()

    # Run impact matching
    from app.services.matching import run_impact_analysis
    matches = run_impact_analysis(db, demo_run.id, req_objs)

    impact_objs = []
    for match in matches:
        impact = ImpactResult(
            analysis_run_id=demo_run.id,
            requirement_id=match["requirement_id"],
            catalogue_item_id=match["catalogue_item_id"],
            match_reason=match["match_reason"],
            confidence=match["confidence"],
            suggested_action=match["suggested_action"],
            is_demo=True,
        )
        db.add(impact)
        impact_objs.append(impact)
    db.flush()

    # Log audit event
    db.add(AuditEvent(
        event_type="demo_scenario_loaded",
        record_id=demo_doc.id,
        record_type="document",
        details=f"Demo scenario loaded: {len(req_objs)} requirements, {len(impact_objs)} impact results",
        is_demo_related=True,
    ))

    db.commit()

    return {
        "document_id": demo_doc.id,
        "analysis_run_id": demo_run.id,
        "requirements_count": len(req_objs),
        "impact_results_count": len(impact_objs),
    }


def reset_demo_data(db: Session) -> dict:
    """
    Remove all demo records (documents, analyses, requirements, impacts, tickets).
    Preserves all non-demo records and ALL audit events.
    Returns counts of deleted records.
    """
    # Count before deletion
    tickets_deleted = db.query(ChangeTicket).filter(ChangeTicket.is_demo == True).count()
    impacts_deleted = db.query(ImpactResult).filter(ImpactResult.is_demo == True).count()
    reqs_deleted = db.query(Requirement).filter(Requirement.is_demo == True).count()
    runs_deleted = db.query(AnalysisRun).filter(AnalysisRun.is_demo == True).count()
    docs_deleted = db.query(Document).filter(Document.is_demo == True).count()

    # Delete in FK order
    db.query(ChangeTicket).filter(ChangeTicket.is_demo == True).delete()
    db.query(ImpactResult).filter(ImpactResult.is_demo == True).delete()
    db.query(Requirement).filter(Requirement.is_demo == True).delete()
    db.query(AnalysisRun).filter(AnalysisRun.is_demo == True).delete()
    db.query(Document).filter(Document.is_demo == True).delete()

    # Log the reset as an audit event (preserved)
    db.add(AuditEvent(
        event_type="demo_scenario_reset",
        details=f"Demo data cleared: {docs_deleted} docs, {reqs_deleted} reqs, {impacts_deleted} impacts, {tickets_deleted} tickets",
        is_demo_related=True,
    ))

    db.commit()

    return {
        "documents_deleted": docs_deleted,
        "analysis_runs_deleted": runs_deleted,
        "requirements_deleted": reqs_deleted,
        "impact_results_deleted": impacts_deleted,
        "tickets_deleted": tickets_deleted,
    }
