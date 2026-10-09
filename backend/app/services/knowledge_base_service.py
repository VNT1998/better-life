import logging
import math
import re
from typing import List, Dict, Any, Optional
from app.db.session import SessionLocal
from app.db.models import GuidelineChunkModel
from app.schemas.clinical import (
    GuidelineChunk,
    EvidenceCitation,
    RAGQueryResponse,
    ObservationValue,
    ObservationFlag,
    FindingWithEvidence,
)

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """
    Evidence-grounded Clinical Guideline Knowledge Base & RAG service.
    Retrieves authoritative clinical guideline evidence chunks and grounds findings with verifiable citations.
    """

    def search_guidelines(
        self,
        query: str,
        top_k: int = 3,
        db_session: Optional[Any] = None,
    ) -> List[tuple[GuidelineChunkModel, float]]:
        """
        Retrieves relevant clinical guideline chunks for a query using TF-IDF / BM25 style lexical scoring.
        """
        should_close = False
        db = db_session
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            chunks = db.query(GuidelineChunkModel).all()
            if not chunks:
                return []

            query_tokens = [w.lower() for w in re.findall(r"\b\w{3,}\b", query.lower())]
            if not query_tokens:
                return [(chunks[0], 0.5)]

            scored: List[tuple[GuidelineChunkModel, float]] = []

            for chunk in chunks:
                haystack = f"{chunk.title} {chunk.section} {chunk.keywords or ''} {chunk.text}".lower()
                chunk_tokens = re.findall(r"\b\w{3,}\b", haystack)
                total_words = max(len(chunk_tokens), 1)

                # Token matching and category boosting
                score = 0.0
                for q in query_tokens:
                    count = haystack.count(q)
                    if count > 0:
                        # Term frequency with diminishing returns
                        score += 1.0 + math.log1p(count)

                # Bonus for exact phrase or keyword matches
                if chunk.keywords and any(q in chunk.keywords.lower() for q in query_tokens):
                    score += 2.0

                normalized_score = min(0.99, round(score / (len(query_tokens) * 2.5 + 1.0), 3))
                if normalized_score > 0.15:
                    scored.append((chunk, normalized_score))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]
        finally:
            if should_close:
                db.close()

    def query_rag(self, query: str, top_k: int = 3) -> RAGQueryResponse:
        results = self.search_guidelines(query, top_k=top_k)
        chunks: List[GuidelineChunk] = []
        citations: List[EvidenceCitation] = []

        for c, score in results:
            chunk_dto = GuidelineChunk(
                id=c.id,
                knowledge_base_id=c.knowledge_base_id,
                title=c.title,
                organization=c.organization,
                category=c.category,
                section=c.section,
                page=c.page,
                text=c.text,
                recommendation_level=c.recommendation_level,
                publication_year=c.publication_year,
            )
            chunks.append(chunk_dto)
            citations.append(
                EvidenceCitation(
                    claim=f"Guideline recommendations regarding: {query}",
                    guideline_name=c.title,
                    organization=c.organization,
                    section=c.section,
                    page=c.page,
                    relevant_excerpt=c.text[:280] + "...",
                    recommendation_level=c.recommendation_level,
                    similarity_score=score,
                )
            )

        return RAGQueryResponse(
            query=query,
            evidence_chunks=chunks,
            citations=citations,
        )

    def ground_observations_with_evidence(
        self,
        observations: List[ObservationValue],
        db_session: Optional[Any] = None,
    ) -> List[FindingWithEvidence]:
        """
        Takes extracted observations, identifies clinically significant out-of-range values,
        retrieves matching clinical guidelines, and generates evidence-grounded findings with verifiable citations.
        """
        findings: List[FindingWithEvidence] = []

        # Filter to abnormal or out-of-range observations
        abnormal_obs = [
            o for o in observations
            if o.flag in (ObservationFlag.HIGH, ObservationFlag.LOW, ObservationFlag.CRITICAL_HIGH, ObservationFlag.CRITICAL_LOW, ObservationFlag.BORDERLINE)
        ]

        # If all normal, pick 2 key observations (e.g. Hemoglobin or Glucose) to demonstrate grounding
        target_obs = abnormal_obs if abnormal_obs else observations[:2]

        for obs in target_obs:
            query = f"{obs.name} {obs.category} {obs.flag.value} reference range {obs.unit}"
            guideline_matches = self.search_guidelines(query, top_k=2, db_session=db_session)

            citations: List[EvidenceCitation] = []
            for g, score in guideline_matches:
                claim_text = (
                    f"{obs.name} measured at {obs.value} {obs.unit} is classified as {obs.flag.value} "
                    f"relative to standard diagnostic criteria."
                )
                citations.append(
                    EvidenceCitation(
                        claim=claim_text,
                        guideline_name=g.title,
                        organization=g.organization,
                        section=g.section,
                        page=g.page,
                        relevant_excerpt=g.text,
                        recommendation_level=g.recommendation_level,
                        similarity_score=score,
                    )
                )

            risk_level = "High" if "CRITICAL" in obs.flag.value else ("Medium" if obs.flag in (ObservationFlag.HIGH, ObservationFlag.LOW) else "Low")
            rationale = (
                f"{obs.name} value of {obs.value} {obs.unit} (Reference: {obs.reference_range_text or 'standard'}) "
                f"exhibits a {obs.flag.value.lower()} status in source document '{obs.source_document_name or 'Report'}' (Page {obs.page_number or 1})."
            )

            findings.append(
                FindingWithEvidence(
                    finding=f"Altered {obs.name} ({obs.value} {obs.unit}) — {obs.flag.value}",
                    category=obs.category,
                    risk_level=risk_level,
                    clinical_rationale=rationale,
                    citations=citations,
                )
            )

        return findings


knowledge_base_service = KnowledgeBaseService()
