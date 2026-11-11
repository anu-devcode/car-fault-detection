import pytest

from car_fault_detection.api.app import load_detector


def test_research_model_cannot_load_without_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("AUDIO_MODEL_BACKEND", "research_ast")
    monkeypatch.delenv("ALLOW_RESEARCH_MODELS", raising=False)
    with pytest.raises(ValueError, match="explicit local opt-in"):
        load_detector()
