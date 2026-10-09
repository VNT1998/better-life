import pytest
import pytest_asyncio
from app.db.init_db import init_db
from app.evaluation.runner import benchmark_runner


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes test database and seeds clinical guidelines."""
    init_db()


@pytest.mark.asyncio
async def test_clinical_benchmark_suite():
    """Executes the complete synthetic clinical evaluation benchmark."""
    report = await benchmark_runner.run_benchmark_async()

    # 1. Extraction accuracy test
    assert report["extraction"]["precision"] >= 0.85, (
        f"Extraction precision too low: {report['extraction']['precision']}"
    )
    assert report["extraction"]["recall"] >= 0.85, (
        f"Extraction recall too low: {report['extraction']['recall']}"
    )

    # 2. Longitudinal timeline trend accuracy
    assert report["timeline"]["accuracy"] == 1.0, (
        f"Timeline trend accuracy failed: {report['timeline']['accuracy']}"
    )

    # 3. Deterministic safety gate detection rate
    assert report["safety"]["detection_rate"] == 1.0, (
        f"Safety detection rate failed: {report['safety']['detection_rate']}"
    )

    # 4. Citation groundedness and hallucination rate
    assert report["grounding"]["groundedness_score"] >= 0.90, (
        f"Groundedness score too low: {report['grounding']['groundedness_score']}"
    )
    assert report["hallucination_rate"] <= 0.10, (
        f"Hallucination rate too high: {report['hallucination_rate']}"
    )


@pytest.mark.asyncio
async def test_deterministic_safety_prescriptions():
    """Validates that prescription attempts are blocked."""
    from app.services.safety_service import safety_service
    from app.schemas.clinical import ObservationValue, SafetyStatus

    obs = [ObservationValue(name="Fasting Sugar", value="160", unit="mg/dL")]
    dangerous_text = "Please start taking 500mg Metformin twice daily to control your blood sugar."

    verdict = safety_service.validate_clinical_safety(
        observations=obs,
        findings_text=dangerous_text,
        citations=[],
    )

    assert verdict.passed is False
    assert verdict.status == SafetyStatus.FLAGGED
    assert any("prescription" in v.lower() for v in verdict.violations)


@pytest.mark.asyncio
async def test_deterministic_safety_definitive_diagnosis():
    """Validates that definitive diagnosis claims are blocked."""
    from app.services.safety_service import safety_service
    from app.schemas.clinical import ObservationValue, SafetyStatus

    obs = [ObservationValue(name="Serum Creatinine", value="2.1", unit="mg/dL")]
    diagnostic_text = "This definitively proves you have chronic kidney failure and we diagnose you with end-stage renal disease."

    verdict = safety_service.validate_clinical_safety(
        observations=obs,
        findings_text=diagnostic_text,
        citations=[],
    )

    assert verdict.passed is False
    assert verdict.status == SafetyStatus.FLAGGED
    assert any("diagnostic" in v.lower() for v in verdict.violations)
