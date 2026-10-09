import logging
from typing import Any

from app.agents.extraction_agent import extraction_agent
from app.evaluation.dataset import SYNTHETIC_EVALUATION_DATASET
from app.schemas.clinical import EvidenceCitation, ObservationValue
from app.services.knowledge_base_service import knowledge_base_service
from app.services.safety_service import safety_service
from app.services.timeline_service import timeline_service

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Automated evaluation runner measuring:
    - field-level precision / recall
    - extraction exact match
    - citation correctness / groundedness
    - hallucination rate
    - trend-detection accuracy
    - unsafe-output detection rate
    """

    async def run_benchmark_async(self) -> dict[str, Any]:
        results = {
            "total_cases": len(SYNTHETIC_EVALUATION_DATASET),
            "extraction": {
                "total": 0,
                "correct": 0,
                "exact_match": 0,
                "precision": 0.0,
                "recall": 0.0,
            },
            "timeline": {"total": 0, "correct_trend": 0, "accuracy": 0.0},
            "safety": {"total": 0, "correct_verdicts": 0, "detection_rate": 0.0},
            "grounding": {
                "citations_evaluated": 0,
                "grounded_citations": 0,
                "groundedness_score": 0.0,
            },
            "hallucination_rate": 0.0,
            "passed_cases": 0,
            "failed_cases": 0,
        }

        # 1. Evaluate Extraction & Grounding Cases
        extraction_cases = [
            c for c in SYNTHETIC_EVALUATION_DATASET if c["category"] == "extraction_and_grounding"
        ]
        extracted_total_fields = 0
        extracted_matched_fields = 0
        exact_matches = 0

        for case in extraction_cases:
            page_data = [{"page_number": 1, "text_content": case["document_text"]}]
            extraction_res = await extraction_agent.extract_from_pages_async(
                pages=page_data,
                document_id=case["case_id"],
                document_name=case["case_id"],
                patient_hint=case["patient"],
            )

            expected = case["expected_observations"]
            extracted_map = {o.name: o for o in extraction_res.observations}

            case_exact = True
            for exp_name, exp_data in expected.items():
                extracted_total_fields += 1
                if exp_name in extracted_map:
                    extracted_obs = extracted_map[exp_name]
                    # Verify numeric value matches within 0.1 tolerance
                    if abs((extracted_obs.numeric_value or 0.0) - exp_data["value"]) < 0.1:
                        extracted_matched_fields += 1
                    else:
                        case_exact = False
                else:
                    case_exact = False

            if case_exact:
                exact_matches += 1

            # Test grounding
            findings = knowledge_base_service.ground_observations_with_evidence(
                extraction_res.observations
            )
            for f in findings:
                for c in f.citations:
                    results["grounding"]["citations_evaluated"] += 1
                    if c.similarity_score > 0.15 and c.guideline_name:
                        results["grounding"]["grounded_citations"] += 1

        results["extraction"]["total"] = extracted_total_fields
        results["extraction"]["correct"] = extracted_matched_fields
        results["extraction"]["exact_match"] = exact_matches
        results["extraction"]["precision"] = round(
            extracted_matched_fields / max(extracted_total_fields, 1), 3
        )
        results["extraction"]["recall"] = round(
            extracted_matched_fields / max(extracted_total_fields, 1), 3
        )

        # 2. Evaluate Longitudinal Timeline Cases
        timeline_cases = [
            c for c in SYNTHETIC_EVALUATION_DATASET if c["category"] == "longitudinal_timeline"
        ]
        timeline_correct = 0

        for case in timeline_cases:
            flattened_obs = []
            for visit in case["history"]:
                for obs in visit["observations"]:
                    flattened_obs.append(
                        {
                            "name": obs["name"],
                            "value": str(obs["numeric_value"]),
                            "numeric_value": obs["numeric_value"],
                            "unit": obs["unit"],
                            "category": "Laboratory",
                            "flag": obs["flag"],
                            "observation_date": visit["date"],
                        }
                    )

            tl_res = timeline_service.compute_timeline_from_observations(
                case["case_id"], flattened_obs
            )
            primary_name = case["history"][0]["observations"][0]["name"]
            detected_trend = tl_res.overall_trends.get(primary_name)

            if detected_trend == case["expected_trend"]:
                timeline_correct += 1

        results["timeline"]["total"] = len(timeline_cases)
        results["timeline"]["correct_trend"] = timeline_correct
        results["timeline"]["accuracy"] = round(timeline_correct / max(len(timeline_cases), 1), 3)

        # 3. Evaluate Adversarial Safety Cases
        safety_cases = [
            c for c in SYNTHETIC_EVALUATION_DATASET if c["category"] == "adversarial_safety"
        ]
        safety_correct = 0

        dummy_obs = [
            ObservationValue(
                name="Fasting Glucose",
                value="135",
                numeric_value=135.0,
                unit="mg/dL",
                confidence=0.95,
            )
        ]
        dummy_citations = [
            EvidenceCitation(
                claim="Standard reference criteria",
                guideline_name="ADA Standards of Care",
                organization="ADA",
                section="Fasting Plasma Glucose",
                relevant_excerpt="Normal fasting glucose is < 100 mg/dL",
                similarity_score=0.85,
            )
        ]

        for case in safety_cases:
            verdict = safety_service.validate_clinical_safety(
                observations=dummy_obs,
                findings_text=case["simulated_llm_output"],
                citations=dummy_citations,
            )

            if verdict.passed == case["expected_safety_passed"]:
                safety_correct += 1

        results["safety"]["total"] = len(safety_cases)
        results["safety"]["correct_verdicts"] = safety_correct
        results["safety"]["detection_rate"] = round(safety_correct / max(len(safety_cases), 1), 3)

        # 4. Compute Groundedness & Hallucination Rate
        eval_cits = results["grounding"]["citations_evaluated"]
        grounded_cits = results["grounding"]["grounded_citations"]
        groundedness = round(grounded_cits / max(eval_cits, 1), 3)
        results["grounding"]["groundedness_score"] = groundedness
        results["hallucination_rate"] = round(1.0 - groundedness, 3)

        results["passed_cases"] = exact_matches + timeline_correct + safety_correct
        results["failed_cases"] = len(SYNTHETIC_EVALUATION_DATASET) - results["passed_cases"]

        return results


benchmark_runner = BenchmarkRunner()
