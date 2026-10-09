from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import GuidelineChunkModel
from app.schemas.clinical import (
    KnowledgeBaseResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    GuidelineChunk,
)
from app.services.knowledge_base_service import knowledge_base_service

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=List[KnowledgeBaseResponse])
def list_knowledge_bases(db: Session = Depends(get_db)):
    """Lists indexed clinical guideline knowledge bases and chunk counts."""
    count = db.query(GuidelineChunkModel).count()
    return [
        KnowledgeBaseResponse(
            id="clinical-standards-v1",
            name="Clinical Practice Guidelines & Diagnostic Standards",
            description="Authoritative reference intervals from ADA, AHA/ACC, KDIGO, WHO, and ASH.",
            version="2026.1",
            chunk_count=count,
        )
    ]


@router.post("/{kb_id}/query", response_model=RAGQueryResponse)
def query_knowledge_base(
    kb_id: str,
    req: RAGQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Performs similarity search against the clinical knowledge base,
    returning matching guideline sections, recommendation grades, and verifiable excerpts.
    """
    res = knowledge_base_service.query_rag(query=req.query, top_k=req.top_k)
    return res
