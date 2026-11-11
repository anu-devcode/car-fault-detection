import io
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

from car_fault_detection.api.app import create_app
from car_fault_detection.api.vehicles import MAX_PHOTO_BYTES
from car_fault_detection.vehicles.resources import VehicleProfile, owner_resources
from car_fault_detection.vehicles.vision import VehicleRecognizer


def test_any_manual_make_is_accepted_without_inventing_specs():
    resource = owner_resources(VehicleProfile(make="Unlisted Make", model="Custom Car"))
    assert resource["resources"] == []
    assert "engine" in resource["unknown_fields"]
    assert resource["identity_status"] == "user_provided_not_independently_verified"
    assert owner_resources(VehicleProfile(make=" Toyota ", model="Corolla"))["resources"][0][
        "url"
    ].startswith("https://www.toyota.com/")
    with pytest.raises(ValidationError):
        VehicleProfile(make=" ", model="test")


def test_photo_service_is_optional_and_manual_entry_still_works():
    with TestClient(create_app(lambda: None, lambda: None)) as client:
        assert client.get("/vehicles/vision/status").json()["ready"] is False
        assert (
            client.post("/vehicles/identify", files={"file": ("car.png", b"fake")}).status_code
            == 503
        )
        response = client.post(
            "/vehicles/resources", json={"make": "Suzuki", "model": "Swift", "year": 2016}
        )
        assert response.status_code == 200
        assert response.json()["unknown_fields"]


def test_photo_size_errors_and_decoder_errors():
    def invalid(_):
        raise ValueError("Invalid photo")

    with TestClient(create_app(lambda: None, lambda: SimpleNamespace(predict=invalid))) as client:
        assert (
            client.post(
                "/vehicles/identify", files={"file": ("car.jpg", b"x" * (MAX_PHOTO_BYTES + 1))}
            ).status_code
            == 413
        )
        assert (
            client.post(
                "/vehicles/identify", files={"file": ("car.jpg", b"not a photo")}
            ).status_code
            == 422
        )


def test_unsupported_or_invalid_images_are_rejected_before_model_use():
    recognizer = VehicleRecognizer.__new__(VehicleRecognizer)
    for content in [b"not an image", _tiny_image()]:
        with pytest.raises(ValueError):
            recognizer.predict(content)


def _tiny_image():
    content = io.BytesIO()
    Image.new("RGB", (10, 10)).save(content, format="PNG")
    return content.getvalue()
