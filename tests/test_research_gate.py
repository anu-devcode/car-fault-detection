import pytest

from car_fault_detection.api.app import load_detector


@pytest.mark.parametrize("backend", ["research_ast", "research_crnn"])
def test_research_model_cannot_load_without_explicit_opt_in(monkeypatch, backend):
    monkeypatch.setenv("AUDIO_MODEL_BACKEND", backend)
    monkeypatch.delenv("ALLOW_RESEARCH_MODELS", raising=False)
    with pytest.raises(ValueError, match="explicit local opt-in"):
        load_detector()
