"""
Documents router — upload, list, retrieve.
"""
import os
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, AuditEvent
from app.schemas import DocumentOut
from app.services.extraction import extract_text
from app.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
}
MAX_SIZE_BYTES = settings.max_upload_size_mb * 1024 * 1024


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF or TXT document for analysis."""
    # Validate file type
    if file.content_type not in ALLOWED_TYPES and not (
        file.filename and (file.filename.endswith(".pdf") or file.filename.endswith(".txt"))
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Only PDF and TXT files are accepted.",
        )

    # Determine file type from content type or filename
    file_type = file.content_type
    if file_type not in ALLOWED_TYPES:
        if file.filename and file.filename.endswith(".pdf"):
            file_type = "application/pdf"
        else:
            file_type = "text/plain"

    # Read file content and check size
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if file_size > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum allowed size is {settings.max_upload_size_mb} MB.",
        )

    # Generate safe filename
    ext = ALLOWED_TYPES.get(file_type, ".txt")
    safe_filename = f"{uuid.uuid4().hex}{ext}"

    # Save to disk
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create DB record
    doc = Document(
        filename=safe_filename,
        original_name=file.filename or "unnamed",
        file_type=file_type,
        file_size=file_size,
        status="processing",
        is_demo=False,
    )
    db.add(doc)
    db.flush()

    # Extract text immediately (synchronous for simplicity)
    extracted_text, extraction_error = extract_text(file_path, file_type)

    if extraction_error:
        doc.status = "error"
        doc.extraction_error = extraction_error
    elif not extracted_text.strip():
        doc.status = "error"
        doc.extraction_error = "No text content could be extracted from this file."
    else:
        doc.status = "ready"
        doc.extracted_text = extracted_text

    # Audit event
    db.add(AuditEvent(
        event_type="document_uploaded",
        record_id=doc.id,
        record_type="document",
        details=f"Uploaded '{doc.original_name}' ({file_size} bytes). Status: {doc.status}",
        is_demo_related=False,
    ))

    db.commit()
    db.refresh(doc)

    result = DocumentOut.model_validate(doc)
    result.has_text = bool(doc.extracted_text and doc.extracted_text.strip())
    return result


@router.get("/", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    """List all documents ordered by upload time descending."""
    docs = db.query(Document).order_by(Document.upload_timestamp.desc()).all()
    results = []
    for doc in docs:
        out = DocumentOut.model_validate(doc)
        out.has_text = bool(doc.extracted_text and doc.extracted_text.strip())
        results.append(out)
    return results


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document metadata and extraction status."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    out = DocumentOut.model_validate(doc)
    out.has_text = bool(doc.extracted_text and doc.extracted_text.strip())
    return out


@router.get("/{document_id}/text")
def get_document_text(document_id: int, db: Session = Depends(get_db)):
    """Get extracted text of a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc.extracted_text:
        raise HTTPException(status_code=404, detail="No extracted text available for this document.")
    return {"document_id": document_id, "text": doc.extracted_text, "truncated": False}
