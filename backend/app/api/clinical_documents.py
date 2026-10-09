from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Document, DocumentPage
from app.schemas.clinical import DocumentResponse, DocumentPageSchema
from app.services.ingestion_service import ingestion_service
from app.services.audit_service import audit_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Uploads and segments a clinical document (PDF, Text, or Image).
    Preserves page breaks, character counts, and provenance tokens.
    """
    content = await file.read()
    result = ingestion_service.process_and_store_document(
        content=content,
        filename=file.filename,
        db_session=db,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to process document"),
        )

    doc_id = result["document_id"]
    doc = db.query(Document).filter(Document.id == doc_id).first()

    audit_service.log_event(
        event_type="DOCUMENT_UPLOADED",
        payload={"filename": file.filename, "pages": result["page_count"], "size_bytes": len(content)},
        db_session=db,
    )

    pages = [
        DocumentPageSchema(
            page_number=p.page_number,
            char_count=p.char_count,
            text_preview=p.text_content[:300].strip(),
            text_content=p.text_content,
        )
        for p in doc.pages
    ]

    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        page_count=doc.page_count,
        created_at=doc.created_at,
        pages=pages,
        metadata=doc.metadata_json or {},
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """Lists all ingested clinical documents."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    res = []
    for d in docs:
        pages = [
            DocumentPageSchema(
                page_number=p.page_number,
                char_count=p.char_count,
                text_preview=p.text_content[:200].strip(),
            )
            for p in d.pages
        ]
        res.append(
            DocumentResponse(
                id=d.id,
                filename=d.filename,
                file_type=d.file_type,
                page_count=d.page_count,
                created_at=d.created_at,
                pages=pages,
                metadata=d.metadata_json or {},
            )
        )
    return res


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Fetches document metadata, page segmentation, and text content."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    pages = [
        DocumentPageSchema(
            page_number=p.page_number,
            char_count=p.char_count,
            text_preview=p.text_content[:300].strip(),
            text_content=p.text_content,
        )
        for p in doc.pages
    ]

    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        page_count=doc.page_count,
        created_at=doc.created_at,
        pages=pages,
        metadata=doc.metadata_json or {},
    )
