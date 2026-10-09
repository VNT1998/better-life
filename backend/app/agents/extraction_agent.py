import json
import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.agents.model_manager import ModelManager
from app.schemas.clinical import (
    ClinicalExtractionResult,
    ObservationValue,
    MedicationItem,
    ConditionItem,
    ObservationFlag,
)

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a specialized clinical extraction model.
Your task is to extract structured clinical information from medical laboratory reports and documents.
Return ONLY valid JSON matching this exact structure:
{
  "patient": {
    "name": "...",
    "age": 45,
    "gender": "Male",
    "report_date": "2024-05-18"
  },
  "dates": ["2024-05-18"],
  "observations": [
    {
      "code": "HEMOGLOBIN",
      "name": "Hemoglobin",
      "category": "Hematology",
      "value": "11.2",
      "numeric_value": 11.2,
      "unit": "g/dL",
      "reference_low": 12.0,
      "reference_high": 16.0,
      "reference_range_text": "12.0 - 16.0",
      "flag": "LOW",
      "interpretation": "Mild normocytic anemia",
      "page_number": 1,
      "text_span": "Hemoglobin: 11.2 g/dL (Ref: 12.0 - 16.0)",
      "confidence": 0.98
    }
  ],
  "medications": [],
  "conditions": []
}

Flags must be one of: "NORMAL", "HIGH", "LOW", "CRITICAL_HIGH", "CRITICAL_LOW", "BORDERLINE", "ABNORMAL".
Extract every test result with its name, numeric value, unit, reference range, and flag.
Preserve the page number and text span where found.
Do not output conversational commentary, only the JSON block."""


class ClinicalExtractionAgent:
    """
    Structured Clinical Extraction Agent.
    Transforms raw document pages into normalized Pydantic schemas with full provenance.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()

    async def extract_from_pages_async(
        self,
        pages: List[Dict[str, Any]],
        document_id: str,
        document_name: str,
        patient_hint: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> ClinicalExtractionResult:
        execution_id = f"exec-{uuid.uuid4().hex[:12]}"
        start_time = datetime.now(timezone.utc)

        # Format prompt with page demarcations
        formatted_pages = []
        for p in pages:
            page_num = p.get("page_number", 1)
            content = p.get("text_content", "")
            formatted_pages.append(f"--- [PAGE {page_num}] ---\n{content}")

        doc_payload = "\n\n".join(formatted_pages)
        user_prompt = f"Extract all structured lab results, dates, patient details, medications, and conditions from this document:\n\n{doc_payload}"

        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # Call Model Manager
        model_result = await self.model_manager.generate_chat_completion_async(
            messages=messages,
            model=model,
            temperature=0.1,  # Low temperature for deterministic structured extraction
            max_tokens=3000,
        )

        model_name = model_result.get("model_used") or "ollama-clinical-v1"
        extracted_json = None

        if model_result.get("success"):
            raw_content = model_result.get("content", "").strip()
            extracted_json = self._parse_json_from_text(raw_content)

        # Fallback to deterministic regex extractor if model did not produce valid JSON
        if not extracted_json:
            logger.info(f"Using deterministic clinical extractor fallback for {document_name}")
            extracted_json = self._deterministic_extract(pages, patient_hint)

        # Normalize and construct ClinicalExtractionResult
        return self._normalize_extraction(
            extracted_json=extracted_json,
            document_id=document_id,
            document_name=document_name,
            model_name=model_name,
            execution_id=execution_id,
            patient_hint=patient_hint,
        )

    def _parse_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Cleans and extracts JSON block from markdown."""
        if not text:
            return None

        # Check for ```json ... ``` blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            candidate = json_match.group(1).strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # Check for curly brace boundaries
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        return None

    def _deterministic_extract(
        self,
        pages: List[Dict[str, Any]],
        patient_hint: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic regular expression extractor for standard blood panels.
        Guarantees structured extraction even if local LLM is offline or malformed.
        """
        patient_data = patient_hint or {"name": "Patient", "age": 40, "gender": "Unknown"}
        observations: List[Dict[str, Any]] = []
        found_dates: List[str] = []

        # Standard biomarkers and regex patterns
        patterns = [
            (
                "Hemoglobin",
                "Hematology",
                r"(?:hemoglobin|hb|hgb)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(g/dl|g/l)?",
                12.0, 16.0, "g/dL",
            ),
            (
                "Total WBC Count",
                "Hematology",
                r"(?:wbc|white blood cell count|total wbc count)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(?:x\s*10\^?3/ul|/cumm|/ul)?",
                4.0, 11.0, "x10^3/uL",
            ),
            (
                "Platelet Count",
                "Hematology",
                r"(?:platelet count|platelets)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|/cumm|x\s*10\^?3/ul)?",
                150.0, 450.0, "x10^3/uL",
            ),
            (
                "Fasting Blood Sugar",
                "Metabolic",
                r"(?:fasting blood sugar|fasting glucose|fbs|fpg)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(mg/dl|mmol/l)?",
                70.0, 99.0, "mg/dL",
            ),
            (
                "HbA1c",
                "Metabolic",
                r"(?:hba1c|glycated hemoglobin|a1c)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(%)?",
                4.0, 5.6, "%",
            ),
            (
                "Total Cholesterol",
                "Lipids",
                r"(?:total cholesterol|cholesterol total)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?",
                120.0, 200.0, "mg/dL",
            ),
            (
                "LDL Cholesterol",
                "Lipids",
                r"(?:ldl|ldl cholesterol|ldl-c)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?",
                50.0, 100.0, "mg/dL",
            ),
            (
                "HDL Cholesterol",
                "Lipids",
                r"(?:hdl|hdl cholesterol|hdl-c)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?",
                40.0, 60.0, "mg/dL",
            ),
            (
                "Triglycerides",
                "Lipids",
                r"(?:triglycerides|tg)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?",
                50.0, 150.0, "mg/dL",
            ),
            (
                "Serum Creatinine",
                "Renal",
                r"(?:serum creatinine|creatinine)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?",
                0.6, 1.2, "mg/dL",
            ),
            (
                "Blood Urea Nitrogen",
                "Renal",
                r"(?:bun|blood urea nitrogen|urea)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?",
                7.0, 20.0, "mg/dL",
            ),
            (
                "ALT (SGPT)",
                "Hepatic",
                r"(?:alt|sgpt|alanine aminotransferase)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(u/l|iu/l)?",
                7.0, 45.0, "U/L",
            ),
            (
                "AST (SGOT)",
                "Hepatic",
                r"(?:ast|sgot|aspartate aminotransferase)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(u/l|iu/l)?",
                8.0, 40.0, "U/L",
            ),
            (
                "Total Bilirubin",
                "Hepatic",
                r"(?:total bilirubin|bilirubin total)\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?",
                0.2, 1.2, "mg/dL",
            ),
        ]

        date_pattern = re.compile(r"\b(202\d[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]202\d)\b")

        for page in pages:
            page_num = page.get("page_number", 1)
            text = page.get("text_content", "")

            # Look for dates
            date_matches = date_pattern.findall(text)
            for d in date_matches:
                clean_d = d.replace("/", "-")
                if clean_d not in found_dates:
                    found_dates.append(clean_d)

            for name, cat, regex, ref_low, ref_high, default_unit in patterns:
                match = re.search(regex, text, re.IGNORECASE)
                if match:
                    try:
                        val_num = float(match.group(1))
                        unit = match.group(2) if len(match.groups()) >= 2 and match.group(2) else default_unit

                        flag = "NORMAL"
                        if val_num < ref_low:
                            flag = "LOW"
                        elif val_num > ref_high:
                            flag = "HIGH"

                        span_start = max(0, match.start() - 10)
                        span_end = min(len(text), match.end() + 25)
                        text_span = text[span_start:span_end].strip()

                        # Prevent duplicate observation in same extraction
                        if not any(o["name"] == name for o in observations):
                            observations.append({
                                "code": name.upper().replace(" ", "_"),
                                "name": name,
                                "category": cat,
                                "value": str(val_num),
                                "numeric_value": val_num,
                                "unit": unit,
                                "reference_low": ref_low,
                                "reference_high": ref_high,
                                "reference_range_text": f"{ref_low} - {ref_high} {unit}",
                                "flag": flag,
                                "page_number": page_num,
                                "text_span": text_span,
                                "confidence": 0.95,
                            })
                    except Exception:
                        continue

        return {
            "patient": patient_data,
            "dates": found_dates or [datetime.utcnow().strftime("%Y-%m-%d")],
            "observations": observations,
            "medications": [],
            "conditions": [],
        }

    def _normalize_extraction(
        self,
        extracted_json: Dict[str, Any],
        document_id: str,
        document_name: str,
        model_name: str,
        execution_id: str,
        patient_hint: Optional[Dict[str, Any]] = None,
    ) -> ClinicalExtractionResult:
        patient_info = extracted_json.get("patient") or {}
        if patient_hint:
            patient_info.update({k: v for k, v in patient_hint.items() if v})

        raw_observations = extracted_json.get("observations") or extracted_json.get("lab_results") or []
        parsed_observations: List[ObservationValue] = []

        for obs in raw_observations:
            val_raw = str(obs.get("value", ""))
            num_val = obs.get("numeric_value")
            if num_val is None:
                try:
                    num_val = float(re.sub(r"[^\d.]", "", val_raw))
                except Exception:
                    num_val = None

            flag_str = str(obs.get("flag", "NORMAL")).upper()
            try:
                flag_enum = ObservationFlag[flag_str]
            except Exception:
                flag_enum = ObservationFlag.NORMAL

            parsed_obs = ObservationValue(
                code=obs.get("code") or obs.get("name", "").upper().replace(" ", "_"),
                name=obs.get("name", "Unknown Observation"),
                category=obs.get("category", "Laboratory"),
                value=val_raw,
                numeric_value=num_val,
                unit=obs.get("unit", ""),
                reference_low=obs.get("reference_low"),
                reference_high=obs.get("reference_high"),
                reference_range_text=obs.get("reference_range_text"),
                flag=flag_enum,
                interpretation=obs.get("interpretation"),
                source_document_id=document_id,
                source_document_name=document_name,
                page_number=obs.get("page_number", 1),
                text_span=obs.get("text_span"),
                confidence=float(obs.get("confidence", 0.95)),
            )
            parsed_observations.append(parsed_obs)

        # Parse medications and conditions if any
        meds = [MedicationItem(**m) for m in extracted_json.get("medications", []) if isinstance(m, dict)]
        conds = [ConditionItem(**c) for c in extracted_json.get("conditions", []) if isinstance(c, dict)]
        dates = [str(d) for d in extracted_json.get("dates", [])]

        return ClinicalExtractionResult(
            patient=patient_info,
            observations=parsed_observations,
            medications=meds,
            conditions=conds,
            lab_results=parsed_observations,
            dates=dates,
            model_name=model_name,
            model_version="1.0.0",
            prompt_version="v2.0",
            execution_id=execution_id,
            extraction_timestamp=datetime.now(timezone.utc),
        )


extraction_agent = ClinicalExtractionAgent()
