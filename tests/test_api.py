from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from car_fault_detection.api.app import MAX_AUDIO_SIZE_BYTES, create_app


class Detector:
    classes = ["Normal", "Oil system"]

    def __init__(self, error=None):
        self.error = error
        self.paths = []

    def predict_details(self, path):
        self.paths.append(path)
        assert Path(path).exists()
        if self.error:
            raise self.error
        return SimpleNamespace(fault_class="Normal", location="Normal", confidence=0.73)


def test_readiness_and_legacy_health_contract():
    def unavailable():
        raise RuntimeError("bad checkpoint")

    with TestClient(create_app(unavailable)) as client:
        assert client.get("/").json()["model"] == "not loaded"
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
        assert client.get("/classes").status_code == 503
        assert client.post("/predict", files={"file": ("test.wav", b"x" * 2048)}).status_code == 503


def test_success_returns_real_confidence_and_removes_upload():
    detector = Detector()
    with TestClient(create_app(lambda: detector)) as client:
        assert client.get("/ready").status_code == 200
        assert client.get("/classes").json()["classes"] == detector.classes
        result = client.post("/predict", files={"file": ("test.wav", b"x" * 2048, "audio/wav")})
        assert result.status_code == 200
        assert result.json()["confidence"] == 0.73
        assert result.json()["is_normal"] is True
    assert all(not Path(path).exists() for path in detector.paths)


def test_decode_errors_do_not_return_success_and_always_cleanup():
    detector = Detector(ValueError("invalid audio contents"))
    with TestClient(create_app(lambda: detector)) as client:
        result = client.post("/predict", files={"file": ("test.wav", b"x" * 2048)})
        assert result.status_code == 422
    assert all(not Path(path).exists() for path in detector.paths)


def test_unexpected_errors_are_not_exposed_and_always_cleanup():
    detector = Detector(RuntimeError("private model filesystem details"))
    with TestClient(create_app(lambda: detector)) as client:
        result = client.post("/predict", files={"file": ("test.wav", b"x" * 2048)})
        assert result.status_code == 500
        assert "private" not in result.text
    assert all(not Path(path).exists() for path in detector.paths)


def test_upload_bounds_and_type():
    with TestClient(create_app(Detector)) as client:
        for name, content, mime, status in [
            ("empty.wav", b"", "audio/wav", 400),
            ("notes.txt", b"x" * 2048, "text/plain", 400),
            ("large.wav", b"x" * (MAX_AUDIO_SIZE_BYTES + 1), "audio/wav", 413),
        ]:
            assert (
                client.post("/predict", files={"file": (name, content, mime)}).status_code == status
            )


def test_cors_uses_configured_origin(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://car-fault-detection.vercel.app")
    with TestClient(create_app(Detector)) as client:
        allowed = client.options(
            "/predict",
            headers={
                "Origin": "https://car-fault-detection.vercel.app",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert (
            allowed.headers["access-control-allow-origin"]
            == "https://car-fault-detection.vercel.app"
        )
        denied = client.options(
            "/predict",
            headers={
                "Origin": "https://unconfigured.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert denied.status_code == 400
