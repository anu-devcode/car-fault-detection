import os
from dataclasses import dataclass

import joblib
import numpy as np
import torch

from car_fault_detection import config
from car_fault_detection.audio import preprocessing
from car_fault_detection.ml import model


@dataclass(frozen=True)
class Prediction:
    fault_class: str
    location: str
    confidence: float


class EngineFaultDetector:
    def __init__(self, model_path, le_path):
        self.model_path = model_path
        self.le_path = le_path
        self.model_mtime = os.path.getmtime(model_path)

        # Load Label Encoder
        self.le = joblib.load(le_path)
        self.classes = self.le.classes_

        # Load Model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net = model.build_model(len(self.classes))
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
        # Refuse partially loaded/random parameters: readiness must mean a usable checkpoint.
        self.net.load_state_dict(checkpoint, strict=True)
        self.net.to(self.device)
        self.net.eval()

    def predict(self, audio_file):
        """Compatibility API used by the local dashboard and inference demo."""
        prediction = self.predict_details(audio_file)
        return prediction.fault_class, prediction.location

    def predict_details(self, audio_file):
        """Return model softmax confidence, not a calibrated diagnostic probability."""
        # Preprocess
        feature = preprocessing.extract_mel_spectrogram(audio_file)
        if feature is None:
            raise ValueError("Unable to decode audio")

        # Prepare for model (batch_size=1, channel=1, H, W)
        feature = np.expand_dims(feature, axis=(0, 1))
        feature_tensor = torch.tensor(feature, dtype=torch.float32).to(self.device)

        # Predict
        with torch.no_grad():
            outputs = self.net(feature_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = probabilities.max(1)

        class_idx = predicted.item()
        fault_class = self.classes[class_idx]

        # Map to fault location
        location = config.FAULT_MAPPING.get(fault_class, fault_class)

        return Prediction(str(fault_class), str(location), float(confidence.item()))


def run_inference_demo(audio_file):
    detector = EngineFaultDetector(
        os.path.join(config.MODELS_DIR, "best_model.pth"),
        os.path.join(config.MODELS_DIR, "label_encoder.joblib"),
    )
    fault, location = detector.predict(audio_file)
    print(f"\nInference for {audio_file}:")
    print(f"Detected Fault: {fault}")
    print(f"Potential Location: {location}")
    return fault, location
