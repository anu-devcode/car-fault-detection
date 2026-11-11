import numpy as np
import pytest
import torch

from car_fault_detection.ml import inference


def test_invalid_audio_is_not_returned_as_an_error_prediction(monkeypatch):
    detector = inference.EngineFaultDetector.__new__(inference.EngineFaultDetector)
    monkeypatch.setattr(inference.preprocessing, "extract_mel_spectrogram", lambda _: None)
    with pytest.raises(ValueError, match="decode"):
        detector.predict_details("invalid.wav")


def test_confidence_is_derived_from_logits_and_grouped_label_is_preserved(monkeypatch):
    detector = inference.EngineFaultDetector.__new__(inference.EngineFaultDetector)
    detector.device = torch.device("cpu")
    detector.classes = ["Normal", "Oil system"]
    detector.net = lambda _: torch.tensor([[0.0, 2.0]])
    monkeypatch.setattr(
        inference.preprocessing, "extract_mel_spectrogram", lambda _: np.zeros((128, 128))
    )
    result = detector.predict_details("fixture.wav")
    assert result.fault_class == "Oil system"
    assert result.location == "Oil system"
    assert result.confidence == pytest.approx(torch.softmax(torch.tensor([0.0, 2.0]), 0)[1].item())
    assert detector.predict("fixture.wav") == ("Oil system", "Oil system")


def test_checkpoint_loading_is_strict(monkeypatch):
    class Network:
        def load_state_dict(self, state, strict):
            assert strict is True
            raise RuntimeError("size mismatch")

    monkeypatch.setattr(inference.os.path, "getmtime", lambda _: 0)
    monkeypatch.setattr(
        inference.joblib, "load", lambda _: type("Encoder", (), {"classes_": ["Normal"]})()
    )
    monkeypatch.setattr(inference.model, "build_model", lambda _: Network())
    monkeypatch.setattr(inference.torch, "load", lambda *args, **kwargs: {})
    with pytest.raises(RuntimeError, match="mismatch"):
        inference.EngineFaultDetector("checkpoint.pth", "labels.joblib")
