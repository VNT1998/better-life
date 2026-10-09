import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
from app.db.session import SessionLocal
from app.db.models import Observation, Patient
from app.schemas.clinical import (
    BiomarkerTimeline,
    BiomarkerDataPoint,
    PatientTimelineResponse,
    TrendDirection,
    ObservationFlag,
)

logger = logging.getLogger(__name__)


class TimelineService:
    """
    Longitudinal clinical data modeling and trend analysis engine.
    Analyzes biomarker trajectories over time (rising, falling, stable, new, missing).
    """

    def get_patient_timeline(
        self,
        patient_id: str,
        db_session: Optional[Any] = None,
    ) -> PatientTimelineResponse:
        should_close = False
        db = db_session
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            # Query observations for patient ordered chronologically
            observations = (
                db.query(Observation)
                .filter(Observation.patient_id == patient_id)
                .order_by(Observation.created_at.asc())
                .all()
            )

            return self.compute_timeline_from_observations(patient_id, observations)
        finally:
            if should_close:
                db.close()

    def compute_timeline_from_observations(
        self,
        patient_id: str,
        observations: List[Any],
    ) -> PatientTimelineResponse:
        # Group observations by normalized biomarker name
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        all_dates = set()

        for obs in observations:
            name = getattr(obs, "name", None) or obs.get("name")
            if not name:
                continue

            date_str = (
                getattr(obs, "observation_date", None)
                or (obs.created_at.strftime("%Y-%m-%d") if hasattr(obs, "created_at") and obs.created_at else None)
                or obs.get("observation_date")
                or "2024-01-01"
            )
            all_dates.add(date_str)

            val_raw = getattr(obs, "value_raw", None) or obs.get("value") or obs.get("value_raw") or "0"
            num_val = getattr(obs, "numeric_value", None)
            if num_val is None and isinstance(obs, dict):
                num_val = obs.get("numeric_value")

            unit = getattr(obs, "unit", "") or obs.get("unit", "")
            cat = getattr(obs, "category", "Laboratory") or obs.get("category", "Laboratory")
            flag_str = getattr(obs, "flag", "NORMAL") or obs.get("flag", "NORMAL")
            doc_id = getattr(obs, "document_id", None) or obs.get("document_id")

            try:
                flag = ObservationFlag[str(flag_str).upper()]
            except Exception:
                flag = ObservationFlag.NORMAL

            grouped[name].append({
                "date": date_str,
                "value": val_raw,
                "numeric_value": float(num_val) if num_val is not None else None,
                "unit": unit,
                "category": cat,
                "flag": flag,
                "document_id": doc_id,
            })

        timelines: List[BiomarkerTimeline] = []
        overall_trends: Dict[str, str] = {}
        sorted_dates = sorted(list(all_dates))

        for biomarker_name, data_list in grouped.items():
            # Sort data points for this biomarker chronologically
            data_list.sort(key=lambda x: x["date"])
            data_points = [
                BiomarkerDataPoint(
                    date=d["date"],
                    value=d["value"],
                    numeric_value=d["numeric_value"],
                    unit=d["unit"],
                    flag=d["flag"],
                    document_id=d["document_id"],
                )
                for d in data_list
            ]

            category = data_list[0]["category"]
            unit = data_list[0]["unit"]

            trend, delta, pct_change, note = self._calculate_trend(data_points, biomarker_name)
            timelines.append(
                BiomarkerTimeline(
                    biomarker_name=biomarker_name,
                    category=category,
                    unit=unit,
                    data_points=data_points,
                    trend=trend,
                    delta=delta,
                    percentage_change=pct_change,
                    clinical_note=note,
                )
            )
            overall_trends[biomarker_name] = trend.value

        return PatientTimelineResponse(
            patient_id=patient_id,
            recorded_dates=sorted_dates,
            timelines=timelines,
            overall_trends=overall_trends,
        )

    def _calculate_trend(
        self,
        points: List[BiomarkerDataPoint],
        name: str,
    ) -> tuple[TrendDirection, Optional[float], Optional[float], Optional[str]]:
        if not points:
            return TrendDirection.MISSING, None, None, "No data points recorded."

        if len(points) == 1:
            pt = points[0]
            note = f"Initial baseline recorded at {pt.value} {pt.unit} ({pt.flag.value})."
            return TrendDirection.NEW, None, None, note

        first = points[-2]
        latest = points[-1]

        if latest.numeric_value is None or first.numeric_value is None:
            return TrendDirection.STABLE, None, None, "Qualitative observation recorded."

        delta = round(latest.numeric_value - first.numeric_value, 2)
        base = first.numeric_value if first.numeric_value != 0 else 1.0
        pct_change = round((delta / base) * 100, 1)

        # Significant threshold is 5% relative change
        if pct_change > 5.0:
            trend = TrendDirection.RISING
            note = f"Rose from {first.numeric_value} to {latest.numeric_value} {latest.unit} (+{pct_change}%) between {first.date} and {latest.date}."
        elif pct_change < -5.0:
            trend = TrendDirection.FALLING
            note = f"Decreased from {first.numeric_value} to {latest.numeric_value} {latest.unit} ({pct_change}%) between {first.date} and {latest.date}."
        else:
            trend = TrendDirection.STABLE
            note = f"Remained stable around {latest.numeric_value} {latest.unit} (change of {pct_change}%)."

        if latest.flag in (ObservationFlag.HIGH, ObservationFlag.CRITICAL_HIGH, ObservationFlag.LOW, ObservationFlag.CRITICAL_LOW):
            note += f" Status is currently flagged as {latest.flag.value}."

        return trend, delta, pct_change, note


timeline_service = TimelineService()
