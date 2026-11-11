"""Opt-in local inference for the research AST transfer head; never a release default."""

import json
from pathlib import Path

import librosa
import numpy as np
import torch

from car_fault_detection.ml.inference import Prediction


class ResearchASTDetector:
    def __init__(self, directory):
        from transformers import ASTFeatureExtractor, ASTModel

        directory = Path(directory)
        report = json.loads((directory / "metrics.json").read_text())
        if report.get("release_allowed") is not False or report["selected_encoder"] != "ast":
            raise ValueError("Expected the explicitly restricted research AST candidate")
        revision = report["candidates"]["ast"]["encoder_revision"]
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
            start = (len(audio) - rate) // 2
            inputs = self.processor(
                audio[start : start + rate], sampling_rate=rate, return_tensors="pt"
            )
        except Exception as exc:
            raise ValueError("Unable to decode research-model input") from exc
        with torch.inference_mode():
            vector = self.net(**inputs).pooler_output[0].numpy()
        logits = self.weight @ ((vector - self.mean) / self.std) + self.bias
        probabilities = np.exp(logits - logits.max())
        probabilities /= probabilities.sum()
        index = int(probabilities.argmax())
        raw = self.classes[index]
        label = {"healthy": "Normal", "engine_knock": "Engine knock", "misfire": "Misfire"}[raw]
        location = "Normal" if raw == "healthy" else "Combustion & Ignition"
        return Prediction(label, location, float(probabilities[index]))
