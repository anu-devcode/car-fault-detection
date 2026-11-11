import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from car_fault_detection.api.app import create_app
from car_fault_detection.care.guidance import CareRequest, build_advice


@pytest.mark.parametrize(
    "symptom",
    [
        "smoke_or_fire",
        "fuel_smell",
        "brake_problem",
        "steering_problem",
        "overheating",
        "oil_pressure_warning",
        "flashing_engine_light",
    ],
)
def test_urgent_symptoms_override_normal_prediction(symptom):
    advice = build_advice(CareRequest(fault_class="Normal", confidence=0.99, symptoms=[symptom]))
    assert advice["severity"] in {"emergency", "stop_and_assist"}
    assert advice["garage_service"] == "towing"
    assert advice["driving_safety"] == "not_determined"
    assert advice["sources"]


def test_normal_is_not_a_safety_certificate_and_uncertainty_escalates():
    assert (
        build_advice(CareRequest(fault_class="Normal", confidence=0.95))["driving_safety"]
        == "not_determined"
    )
    assert (
        build_advice(CareRequest(fault_class="Normal", confidence=0.2))["severity"] == "inspection"
    )
    assert (
        build_advice(CareRequest(fault_class="Braking System", confidence=0.9))["garage_service"]
        == "towing"
    )


def test_unknown_symptom_or_nan_confidence_is_rejected():
    for payload in [{"symptoms": ["invented"]}, {"confidence": float("nan")}]:
        with pytest.raises(ValidationError):
            CareRequest(**payload)


def test_care_does_not_require_a_loaded_model():
    app = create_app(lambda: None)
    with TestClient(app) as client:
        assert client.get("/ready").status_code == 503
        response = client.post("/care/triage", json={"symptoms": ["overheating"]})
        assert response.status_code == 200
        assert response.json()["severity"] == "stop_and_assist"
