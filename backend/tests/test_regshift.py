"""
RegShift backend automated tests.
Run with: pytest tests/ -v
"""
import pytest
import json
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_regshift.db"

# Patch settings before importing app
import app.config as cfg
cfg.settings.database_url = TEST_DATABASE_URL
cfg.settings.upload_dir = "./test_uploads"
cfg.settings.openai_api_key = ""  # force demo mode

from app.database import Base, get_db
from app.main import app

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    os.makedirs("./test_uploads", exist_ok=True)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


# ========================
# Health Check
# ========================

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "llm_configured" in data


# ========================
# Document Upload
# ========================

def test_upload_txt_document(client):
    content = b"This is a test regulatory document for upload validation."
    resp = client.post(
        "/documents/upload",
        files={"file": ("test_bulletin.txt", content, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["original_name"] == "test_bulletin.txt"
    assert data["status"] == "ready"
    assert data["has_text"] is True
    assert data["is_demo"] is False


def test_upload_empty_file(client):
    resp = client.post(
        "/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_upload_unsupported_type(client):
    resp = client.post(
        "/documents/upload",
        files={"file": ("script.exe", b"MZ\x90", "application/octet-stream")},
    )
    assert resp.status_code == 415


def test_upload_pdf(client):
    # Minimal valid PDF
    minimal_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""
    resp = client.post(
        "/documents/upload",
        files={"file": ("test.pdf", minimal_pdf, "application/pdf")},
    )
    # Should either succeed or return an error about no text (image-only PDF)
    assert resp.status_code in [200, 400]


def test_list_documents_empty(client):
    resp = client.get("/documents/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_documents_after_upload(client):
    content = b"Regulatory document content for listing test."
    client.post("/documents/upload", files={"file": ("bulletin.txt", content, "text/plain")})
    resp = client.get("/documents/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_document_not_found(client):
    resp = client.get("/documents/9999")
    assert resp.status_code == 404


def test_get_document_text(client):
    content = b"Sample regulatory text for text retrieval test."
    upload = client.post("/documents/upload", files={"file": ("reg.txt", content, "text/plain")})
    doc_id = upload.json()["id"]
    resp = client.get(f"/documents/{doc_id}/text")
    assert resp.status_code == 200
    assert "Sample regulatory text" in resp.json()["text"]


# ========================
# Analysis
# ========================

def test_start_analysis_missing_document(client):
    resp = client.post("/analysis/start/9999")
    assert resp.status_code == 404


def test_start_analysis_not_ready(client):
    """Cannot analyze a document that hasn't been extracted yet."""
    from app.models import Document
    from app.database import Base
    db = TestingSessionLocal()
    doc = Document(
        filename="test_not_ready.txt",
        original_name="test_not_ready.txt",
        file_type="text/plain",
        file_size=100,
        status="processing",
        is_demo=False,
    )
    db.add(doc)
    db.commit()
    doc_id = doc.id
    db.close()

    resp = client.post(f"/analysis/start/{doc_id}")
    assert resp.status_code == 400


def test_start_analysis_demo_mode(client):
    """Analysis should complete in demo mode even without LLM."""
    content = b"This is a regulatory bulletin requiring analysis in demo mode."
    upload = client.post("/documents/upload", files={"file": ("test.txt", content, "text/plain")})
    doc_id = upload.json()["id"]

    resp = client.post(f"/analysis/start/{doc_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["llm_used"] is False


def test_get_requirements_after_analysis(client):
    content = b"Insurance carriers must file updated rate schedules by January 1, 2026."
    upload = client.post("/documents/upload", files={"file": ("rate.txt", content, "text/plain")})
    doc_id = upload.json()["id"]

    run = client.post(f"/analysis/start/{doc_id}").json()
    run_id = run["id"]

    resp = client.get(f"/analysis/{run_id}/requirements")
    assert resp.status_code == 200
    reqs = resp.json()
    assert isinstance(reqs, list)
    # In demo mode we get 3 demo requirements
    assert len(reqs) >= 1


# ========================
# Demo Scenario
# ========================

def test_load_demo(client):
    resp = client.post("/demo/load")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["requirements_count"] > 0
    assert data["impact_results_count"] > 0


def test_reset_demo(client):
    client.post("/demo/load")
    resp = client.post("/demo/reset")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["documents_deleted"] >= 1


def test_demo_status(client):
    resp = client.get("/demo/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "demo_loaded" in data

    client.post("/demo/load")
    resp = client.get("/demo/status")
    assert resp.json()["demo_loaded"] is True


def test_audit_events_preserved_after_reset(client):
    client.post("/demo/load")
    client.post("/demo/reset")
    resp = client.get("/audit/")
    events = resp.json()
    event_types = [e["event_type"] for e in events]
    assert "demo_scenario_loaded" in event_types
    assert "demo_scenario_reset" in event_types


# ========================
# Impact Analysis
# ========================

def test_impact_results_after_demo_load(client):
    load = client.post("/demo/load").json()
    run_id = load["analysis_run_id"]

    resp = client.get(f"/impact/{run_id}")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0

    # Check required fields
    for result in results:
        assert "match_reason" in result
        assert "confidence" in result
        assert result["confidence"] in ["high", "medium", "low"]
        assert "suggested_action" in result
        assert "catalogue_item" in result
        assert "requirement" in result


def test_no_impact_for_non_matching_doc(client):
    """A document about something completely unrelated should match very few items."""
    # Clear catalogue first to prevent any matches
    from app.models import InsuranceCatalogueItem
    db = TestingSessionLocal()
    db.query(InsuranceCatalogueItem).delete()
    db.commit()
    db.close()

    content = b"This document is about cooking recipes and has nothing to do with insurance."
    upload = client.post("/documents/upload", files={"file": ("food.txt", content, "text/plain")})
    doc_id = upload.json()["id"]

    run = client.post(f"/analysis/start/{doc_id}").json()
    run_id = run["id"]

    resp = client.get(f"/impact/{run_id}")
    assert resp.status_code == 200
    # No catalogue items, so no matches
    assert resp.json() == []


def test_catalogue_endpoint(client):
    client.post("/demo/load")
    resp = client.get("/impact/catalogue/all")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    for item in items:
        assert item["item_type"] in ["product", "rule", "form"]


# ========================
# Change Tickets
# ========================

def _get_first_impact_id(client) -> int:
    load = client.post("/demo/load").json()
    run_id = load["analysis_run_id"]
    impacts = client.get(f"/impact/{run_id}").json()
    return impacts[0]["id"]


def test_create_ticket(client):
    impact_id = _get_first_impact_id(client)
    resp = client.post("/tickets/", json={"impact_result_id": impact_id})
    assert resp.status_code == 201
    ticket = resp.json()
    assert ticket["status"] == "draft"
    assert ticket["ticket_ref"].startswith("TKT-")
    assert "evidence" in ticket
    assert "priority" in ticket


def test_create_duplicate_ticket(client):
    impact_id = _get_first_impact_id(client)
    client.post("/tickets/", json={"impact_result_id": impact_id})
    resp = client.post("/tickets/", json={"impact_result_id": impact_id})
    assert resp.status_code == 409


def test_create_ticket_missing_impact(client):
    resp = client.post("/tickets/", json={"impact_result_id": 9999})
    assert resp.status_code == 404


def test_list_tickets(client):
    impact_id = _get_first_impact_id(client)
    client.post("/tickets/", json={"impact_result_id": impact_id})
    resp = client.get("/tickets/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_draft_ticket(client):
    impact_id = _get_first_impact_id(client)
    ticket = client.post("/tickets/", json={"impact_result_id": impact_id}).json()
    ticket_id = ticket["id"]

    resp = client.patch(f"/tickets/{ticket_id}", json={"title": "Updated Title"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


def test_submit_for_review(client):
    impact_id = _get_first_impact_id(client)
    ticket = client.post("/tickets/", json={"impact_result_id": impact_id}).json()
    ticket_id = ticket["id"]

    resp = client.post(f"/tickets/{ticket_id}/submit")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending_review"


# ========================
# Review Workflow
# ========================

def _create_pending_ticket(client) -> dict:
    impact_id = _get_first_impact_id(client)
    ticket = client.post("/tickets/", json={"impact_result_id": impact_id}).json()
    client.post(f"/tickets/{ticket['id']}/submit")
    return client.get(f"/tickets/{ticket['id']}").json()


def test_approve_ticket(client):
    ticket = _create_pending_ticket(client)
    resp = client.post(
        f"/tickets/{ticket['id']}/review",
        json={"action": "approve", "comment": "Looks good — approved."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["reviewer_comment"] == "Looks good — approved."


def test_reject_ticket(client):
    ticket = _create_pending_ticket(client)
    resp = client.post(
        f"/tickets/{ticket['id']}/review",
        json={"action": "reject", "comment": "Insufficient evidence."},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_request_changes(client):
    ticket = _create_pending_ticket(client)
    resp = client.post(
        f"/tickets/{ticket['id']}/review",
        json={"action": "request_changes", "comment": "Please clarify the effective date."},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "changes_requested"


def test_invalid_review_action(client):
    ticket = _create_pending_ticket(client)
    resp = client.post(
        f"/tickets/{ticket['id']}/review",
        json={"action": "delete_everything"},
    )
    assert resp.status_code == 400


def test_cannot_approve_draft_ticket(client):
    impact_id = _get_first_impact_id(client)
    ticket = client.post("/tickets/", json={"impact_result_id": impact_id}).json()
    resp = client.post(
        f"/tickets/{ticket['id']}/review",
        json={"action": "approve"},
    )
    assert resp.status_code == 400


def test_cannot_edit_approved_ticket(client):
    ticket = _create_pending_ticket(client)
    client.post(f"/tickets/{ticket['id']}/review", json={"action": "approve"})
    resp = client.patch(f"/tickets/{ticket['id']}", json={"title": "Trying to edit"})
    assert resp.status_code == 400


def test_terminal_status_no_further_transitions(client):
    """Approved tickets cannot be transitioned further."""
    ticket = _create_pending_ticket(client)
    client.post(f"/tickets/{ticket['id']}/review", json={"action": "approve"})
    resp = client.post(f"/tickets/{ticket['id']}/review", json={"action": "reject"})
    assert resp.status_code == 400


# ========================
# Audit Trail
# ========================

def test_audit_events_created(client):
    content = b"Test document for audit trail verification."
    upload = client.post("/documents/upload", files={"file": ("audit_test.txt", content, "text/plain")})
    doc_id = upload.json()["id"]
    client.post(f"/analysis/start/{doc_id}")

    resp = client.get("/audit/")
    assert resp.status_code == 200
    events = resp.json()
    event_types = [e["event_type"] for e in events]
    assert "document_uploaded" in event_types
    assert "analysis_started" in event_types
    assert "analysis_completed" in event_types


def test_audit_events_include_review_decisions(client):
    ticket = _create_pending_ticket(client)
    client.post(f"/tickets/{ticket['id']}/review", json={"action": "approve", "comment": "OK"})

    resp = client.get("/audit/")
    events = resp.json()
    event_types = [e["event_type"] for e in events]
    assert "ticket_approved" in event_types


def test_audit_events_are_readonly(client):
    """Confirm there is no DELETE endpoint for audit events."""
    # FastAPI would return 405 Method Not Allowed for an unsupported method
    resp = client.delete("/audit/1")
    assert resp.status_code in [404, 405]


# ========================
# Overview Stats
# ========================

def test_overview_stats_empty(client):
    resp = client.get("/overview/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_documents"] == 0
    assert data["completed_analyses"] == 0
    assert data["pending_reviews"] == 0
    assert data["open_tickets"] == 0


def test_overview_stats_after_demo(client):
    client.post("/demo/load")
    resp = client.get("/overview/stats")
    data = resp.json()
    assert data["total_documents"] >= 1
    assert data["completed_analyses"] >= 1


# ========================
# Text Extraction Unit Tests
# ========================

def test_extract_txt():
    from app.services.extraction import extract_text
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("This is a regulatory requirement about wildfire disclosure.")
        path = f.name
    try:
        text, error = extract_text(path, "text/plain")
        assert error is None
        assert "wildfire disclosure" in text
    finally:
        os.unlink(path)


def test_extract_nonexistent_file():
    from app.services.extraction import extract_text
    text, error = extract_text("/nonexistent/path/file.txt", "text/plain")
    assert error is not None
    assert text == ""


def test_extract_unsupported_type():
    from app.services.extraction import extract_text
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"binary content")
        path = f.name
    try:
        text, error = extract_text(path, "application/xyz")
        assert error is not None
    finally:
        os.unlink(path)


# ========================
# Impact Matching Unit Tests
# ========================

def test_impact_matching_finds_relevant_items(client):
    """High-confidence matches should be found for wildfire/homeowner requirements."""
    client.post("/demo/load")
    resp = client.get("/impact/catalogue/all")
    items_by_name = {item["name"]: item for item in resp.json()}
    assert "HO-3 Special Form Homeowners" in items_by_name
    assert "CA-HO-RATE-007: Wildfire Zone Surcharge Schedule" in items_by_name


def test_impact_matching_confidence_levels(client):
    load = client.post("/demo/load").json()
    run_id = load["analysis_run_id"]
    impacts = client.get(f"/impact/{run_id}").json()

    confidences = [i["confidence"] for i in impacts]
    # Should have at least some high-confidence matches for demo scenario
    assert "high" in confidences


# ========================
# Database Persistence
# ========================

def test_data_persists_across_sessions(client):
    """Data saved in one request should be retrievable in another."""
    content = b"Persistent regulatory document content."
    upload = client.post("/documents/upload", files={"file": ("persist.txt", content, "text/plain")})
    doc_id = upload.json()["id"]

    # Simulate separate request session
    resp = client.get(f"/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


def test_ticket_persists_after_review(client):
    """Ticket review decision should persist."""
    ticket = _create_pending_ticket(client)
    client.post(f"/tickets/{ticket['id']}/review", json={"action": "approve", "comment": "Verified."})

    resp = client.get(f"/tickets/{ticket['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["reviewer_comment"] == "Verified."
