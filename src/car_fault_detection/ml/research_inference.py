"""Opt-in local inference for transfer-learning research heads."""

import json
from pathlib import Path

import librosa
import numpy as np
import torch

from car_fault_detection import config
from car_fault_detection.audio.windows import recording_windows
from car_fault_detection.ml.inference import Prediction
from car_fault_detection.ml.transfer_features import (
    checkpoint_revision,
    crnn_recording_embedding,
    load_crnn_encoder,
)


class ResearchAudioDetector:
    def __init__(self, directory, encoder="ast"):
        directory = Path(directory)
        report = json.loads((directory / "metrics.json").read_text())
        if (
            encoder not in {"ast", "crnn"}
            or report.get("release_allowed") is not False
            or report["selected_encoder"] != encoder
        ):
            raise ValueError("Research head must match the configured encoder")
        self.window_count = report["head_training"].get("windows_per_recording", 1)
        if self.window_count not in {1, 3}:
            raise ValueError("Unsupported research window count")
        revision = report["candidates"][encoder]["encoder_revision"]
        self.encoder = encoder
        if encoder == "crnn":
            model_path = Path(config.MODELS_DIR) / "best_model.pth"
            if checkpoint_revision(model_path) != revision:
                raise ValueError(
                    "The research head was trained against a different CRNN checkpoint"
                )
            self.net = load_crnn_encoder(
                model_path, Path(config.MODELS_DIR) / "label_encoder.joblib"
            )
        else:
            from transformers import ASTFeatureExtractor, ASTModel

            repo = "MIT/ast-finetuned-audioset-10-10-0.4593"
            self.processor = ASTFeatureExtractor.from_pretrained(
                repo, revision=revision, local_files_only=True
            )
            self.net = ASTModel.from_pretrained(
                repo, revision=revision, use_safetensors=True, local_files_only=True
            )
            self.net.eval()
        with np.load(directory / "head.npz", allow_pickle=False) as head:
            self.classes = head["classes"].tolist()
            self.mean, self.std = head["mean"], head["std"]
            self.weight, self.bias = head["weight"], head["bias"]
        if self.classes != report["classes"] or self.weight.shape != (
            len(self.classes),
            self.mean.size,
        ):
            raise ValueError("Research head does not match its report")
        if not all(
            np.isfinite(value).all() for value in [self.mean, self.std, self.weight, self.bias]
        ) or np.any(self.std <= 0):
            raise ValueError("Invalid research head parameters")

    def predict_details(self, audio_file):
        try:
            audio, rate = librosa.load(
                audio_file, sr=16000, mono=True, duration=10, res_type="kaiser_fast"
            )
            if len(audio) < rate or not np.isfinite(audio).all():
                raise ValueError("Research model needs at least one second of valid audio")
            segments = recording_windows(audio, rate, self.window_count)
        except Exception as exc:
            raise ValueError("Unable to decode research-model input") from exc
        if self.encoder == "crnn":
            vector = crnn_recording_embedding(self.net, segments, rate)
        else:
            inputs = self.processor(segments, sampling_rate=rate, return_tensors="pt")
            with torch.inference_mode():
                vector = self.net(**inputs).pooler_output.mean(dim=0).numpy()
        logits = self.weight @ ((vector - self.mean) / self.std) + self.bias
        probabilities = np.exp(logits - logits.max())
        probabilities /= probabilities.sum()
        index = int(probabilities.argmax())
        raw = self.classes[index]
        label = {"healthy": "Normal", "engine_knock": "Engine knock", "misfire": "Misfire"}[raw]
        location = "Normal" if raw == "healthy" else "Combustion & Ignition"
        return Prediction(label, location, float(probabilities[index]))


ResearchASTDetector = ResearchAudioDetector
