"""Keep training and local research inference on the same CRNN preprocessing."""

import hashlib
import io
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from car_fault_detection.audio.preprocessing import extract_mel_spectrogram
from car_fault_detection.ml.inference import EngineFaultDetector


def checkpoint_revision(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_crnn_encoder(model_path, labels_path):
    model = EngineFaultDetector(model_path, labels_path).net.cpu()
    model.classifier = torch.nn.Identity()
    return model.eval()


def crnn_recording_embedding(model, segments, rate):
    features = []
    for segment in segments:
        buffer = io.BytesIO()
        sf.write(buffer, segment, rate, format="WAV", subtype="PCM_16")
        buffer.seek(0)
        mel = extract_mel_spectrogram(buffer)
        if mel is None:
            raise ValueError("Feature extraction failed")
        features.append(mel)
    inputs = torch.tensor(np.stack(features)).float()[:, None]
    with torch.inference_mode():
        return model(inputs).mean(dim=0).numpy()
