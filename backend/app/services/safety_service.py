import re
import logging
from typing import List, Dict, Any, Optional
from app.schemas.clinical import (
    SafetyCheckResult,
    SafetyStatus,
    ObservationValue,
    EvidenceCitation,
)

logger = logging.getLogger(__name__)


class SafetyService:
    """
    Deterministic Safety Architecture and Clinical Rule Engine.
    Enforces non-diagnostic, non-prescriptive, evidence-grounded AI safety boundaries.
    """

    PRESCRIPTION_PATTERNS = [
        r"\b(?:prescribe|administer|take\s+\d+\s*(?:mg|ml|units?|tablets?|capsules?))\b",
        r"\b(?:start\s+taking|dosage\s+of\s+\d+|daily\s+dose\s+of)\b",
        r"\b(?:inject\s+\d+|infuse\s+\d+)\b",
    ]

    DEFINITIVE_DIAGNOSIS_PATTERNS = [
        r"\b(?:you\s+have\s+been\s+diagnosed\s+with|this\s+definitively\s+proves\s+you\s+have)\b",
        r"\b(?:we\s+diagnose\s+you\s+with|confirmed\s+diagnosis\s+of)\b",
        r"\b(?:you\s+are\s+definitely\s+suffering\s+from)\b",
    ]

    IRREVERSIBLE_DECISION_PATTERNS = [
        r"\b(?:stop\s+taking\s+your\s+prescribed|discontinue\s+all\s+medication)\b",
        r"\b(?:ignore\s+your\s+physician|cancel\s+your\s+surgery)\b",
        r"\b(?:do\s+not\s+see\s+a\s+doctor|avoid\s+medical\s+attention)\b",
    ]

    def validate_clinical_safety(
        self,
        observations: List[ObservationValue],
        findings_text: str,
        citations: List[EvidenceCitation],
    ) -> SafetyCheckResult:
        violations: List[str] = []
        checks = {
            "no_prescriptions": True,
            "no_definitive_diagnosis": True,
            "no_irreversible_decisions": True,
            "citations_grounded": True,
            "confidence_threshold_met": True,
        }

        # 1. Rule Check: No Prescriptions or Drug Dosages
        for pattern in self.PRESCRIPTION_PATTERNS:
            if re.search(pattern, findings_text, re.IGNORECASE):
                violations.append("Violation: Output contains specific pharmacological dosing or prescription directives.")
                checks["no_prescriptions"] = False
                break

        # 2. Rule Check: No Definitive Diagnostic Claims
        for pattern in self.DEFINITIVE_DIAGNOSIS_PATTERNS:
            if re.search(pattern, findings_text, re.IGNORECASE):
                violations.append("Violation: Output makes definitive diagnostic claims instead of differential/investigational summaries.")
                checks["no_definitive_diagnosis"] = False
                break

        # 3. Rule Check: No Irreversible Decisions
        for pattern in self.IRREVERSIBLE_DECISION_PATTERNS:
            if re.search(pattern, findings_text, re.IGNORECASE):
                violations.append("Violation: Output advises counter-medical or irreversible clinical decisions.")
                checks["no_irreversible_decisions"] = False
                break

        # 4. Evidence Grounding Check: Citations must be backed by knowledge base
        if citations:
            for c in citations:
                if not c.guideline_name or not c.relevant_excerpt or c.similarity_score < 0.10:
                    violations.append(f"Violation: Citation for '{c.claim}' lacks verifiable grounding in indexed guideline base.")
                    checks["citations_grounded"] = False
                    break

        # 5. Confidence Threshold
        low_confidence_obs = [o for o in observations if o.confidence < 0.70]
        if low_confidence_obs:
            violations.append(f"Confidence Warning: {len(low_confidence_obs)} biomarker(s) have extraction confidence below 0.70 threshold.")
            checks["confidence_threshold_met"] = False

        # Determine Final Safety Verdict
        passed = (
            checks["no_prescriptions"]
            and checks["no_definitive_diagnosis"]
            and checks["no_irreversible_decisions"]
            and checks["citations_grounded"]
        )

        requires_human_review = not passed or not checks["confidence_threshold_met"]

        if passed and not requires_human_review:
            status = SafetyStatus.PASSED
            notes = "All deterministic safety controls satisfied. Output compliant with clinical reference boundaries."
        elif not passed:
            status = SafetyStatus.FLAGGED
            notes = f"Safety violations detected: {'; '.join(violations)}"
        else:
            status = SafetyStatus.REQUIRES_HUMAN_REVIEW
            notes = f"Gated for Human Review: {'; '.join(violations)}"

        return SafetyCheckResult(
            status=status,
            passed=passed,
            violations=violations,
            requires_human_review=requires_human_review,
            checks=checks,
            notes=notes,
        )


safety_service = SafetyService()
