"""Fit a small head over pretrained encoders; select on validation, evaluate once on test."""

import argparse
import copy
import hashlib
import io
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from torch import nn

from car_fault_detection.audio.preprocessing import extract_mel_spectrogram
from car_fault_detection.data.manifest import validate_manifest
from car_fault_detection.ml.inference import EngineFaultDetector


def embeddings(records, root, name, cache):
    cache_path = cache / f"{name}.npz"
    if name == "crnn":
        expected_revision = hashlib.sha256(Path("models/best_model.pth").read_bytes()).hexdigest()
    else:
        from huggingface_hub import model_info

        expected_revision = model_info("MIT/ast-finetuned-audioset-10-10-0.4593").sha
    fingerprint = hashlib.sha256(
        json.dumps(
            {"records": records, "revision": expected_revision, "pipeline": "central-second-v1"},
            sort_keys=True,
        ).encode()
    ).hexdigest()
    if cache_path.exists():
        data = np.load(cache_path, allow_pickle=False)
        if str(data["fingerprint"]) == fingerprint:
            return data["features"], str(data["revision"])
    if name == "crnn":
        detector = EngineFaultDetector("models/best_model.pth", "models/label_encoder.joblib")
        model = detector.net.cpu()
        model.classifier = nn.Identity()
        revision = hashlib.sha256(Path("models/best_model.pth").read_bytes()).hexdigest()
    else:
        from huggingface_hub import model_info
        from transformers import ASTFeatureExtractor, ASTModel

        repo = "MIT/ast-finetuned-audioset-10-10-0.4593"
        revision = expected_revision
        processor = ASTFeatureExtractor.from_pretrained(repo, revision=revision)
        model = ASTModel.from_pretrained(repo, revision=revision, use_safetensors=True)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    features = []
    for index, record in enumerate(records):
        audio, rate = sf.read(root / record["path"], dtype="float32")
        # Same deterministic central second for both encoders; no padding-duration shortcuts.
        start = (len(audio) - rate) // 2
        audio = audio[start : start + rate]
        if name == "crnn":
            buffer = io.BytesIO()
            sf.write(buffer, audio, rate, format="WAV", subtype="PCM_16")
            buffer.seek(0)
            mel = extract_mel_spectrogram(buffer)
            if mel is None:
                raise ValueError("Feature extraction failed")
            inputs = torch.tensor(mel).float()[None, None]
            with torch.inference_mode():
                vector = model(inputs)[0].numpy()
        else:
            values = processor(audio, sampling_rate=rate, return_tensors="pt")
            with torch.inference_mode():
                vector = model(**values).pooler_output[0].numpy()
        features.append(vector)
        if index % 10 == 0:
            print(f"{name} embedding {index + 1}/{len(records)}", flush=True)
    features = np.asarray(features, dtype=np.float32)
    cache.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache_path, features=features, fingerprint=fingerprint, revision=revision)
    return features, revision


def fit_head(features, y, split, classes):
    torch.manual_seed(42)
    train = split == "train"
    validation = split == "validation"
    mean = features[train].mean(0)
    std = np.maximum(features[train].std(0), 1e-6)
    x = torch.tensor((features - mean) / std)
    targets = torch.tensor(y)
    head = nn.Linear(features.shape[1], len(classes))
    optimizer = torch.optim.AdamW(head.parameters(), lr=0.003, weight_decay=0.01)
    best = -1.0
    best_state = None
    best_epoch = 0
    for epoch in range(100):
        head.train()
        optimizer.zero_grad()
        loss = nn.functional.cross_entropy(head(x[train]), targets[train])
        loss.backward()
        optimizer.step()
        with torch.inference_mode():
            prediction = head(x[validation]).argmax(1).numpy()
        score = f1_score(y[validation], prediction, average="macro", zero_division=0)
        if score > best:
            best, best_state, best_epoch = score, copy.deepcopy(head.state_dict()), epoch + 1
    head.load_state_dict(best_state)
    return {
        "head": head,
        "x": x,
        "mean": mean,
        "std": std,
        "validation_macro_f1": best,
        "best_epoch": best_epoch,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/research/kwerimoto"))
    parser.add_argument("--output", type=Path, default=Path("research/transfer-pilot"))
    parser.add_argument("--encoders", nargs="+", choices=["crnn", "ast"], default=["crnn", "ast"])
    args = parser.parse_args()
    torch.set_num_threads(4)
    np.random.seed(42)
    manifest = json.loads((args.dataset / "manifest.json").read_text())
    records = manifest["records"]
    validate_manifest(records)
    for record in records:
        content = (args.dataset / record["path"]).read_bytes()
        if hashlib.sha256(content).hexdigest() != record["file_sha256"]:
            raise ValueError("Dataset content changed after import")
    classes = sorted({record["label"] for record in records})
    y = np.array([classes.index(record["label"]) for record in records])
    split = np.array([record["split"] for record in records])
    candidates = {}
    reports = {}
    started = time.monotonic()
    for name in args.encoders:
        features, revision = embeddings(records, args.dataset, name, args.dataset / "feature_cache")
        candidate = fit_head(features, y, split, classes)
        candidates[name] = candidate
        reports[name] = {key: candidate[key] for key in ["validation_macro_f1", "best_epoch"]}
        reports[name]["encoder_revision"] = revision
        print(name, reports[name], flush=True)
    winner = max(candidates, key=lambda name: candidates[name]["validation_macro_f1"])
    selected = candidates[winner]
    test = split == "test"
    with torch.inference_mode():
        predicted = selected["head"](selected["x"][test]).argmax(1).numpy()
    report = {
        "status": "research_only_not_promoted",
        "release_allowed": False,
        "dataset": manifest["dataset"],
        "dataset_revision": manifest["revision"],
        "selection": manifest["selection"],
        "counts": manifest["counts"],
        "candidates": reports,
        "selected_encoder": winner,
        "selection_metric": "validation_macro_f1; test labels not used in model selection",
        "classes": classes,
        "test_confusion_matrix": confusion_matrix(
            y[test], predicted, labels=range(len(classes))
        ).tolist(),
        "test_report": classification_report(
            y[test],
            predicted,
            labels=range(len(classes)),
            target_names=classes,
            output_dict=True,
            zero_division=0,
        ),
        "majority_baseline_test_accuracy": float(np.max(np.bincount(y[test])) / len(y[test])),
        "head_training": {
            "seed": 42,
            "optimizer": "AdamW",
            "epochs": 100,
            "learning_rate": 0.003,
            "frozen_encoder": True,
            "input": "central 1 second, mono 16 kHz",
            "standardization": "training split only",
        },
        "limitations": manifest["limitations"]
        + [
            "Dataset original rights unverified for release",
            "No non-engine rejection calibration",
            "Existing CRNN pretraining provenance unknown; pretraining overlap cannot be excluded",
            "Published labels may reflect source rather than mechanical condition",
            "AST AudioSet pretraining may overlap pilot clips; not a pretraining-independent benchmark",
            "Exploratory test inspected during development; not a release lockbox",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 1),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2))
    np.savez_compressed(
        args.output / "head.npz",
        weight=selected["head"].weight.detach().numpy(),
        bias=selected["head"].bias.detach().numpy(),
        mean=selected["mean"],
        std=selected["std"],
        classes=np.array(classes),
    )
    # Record provenance without adding raw recordings to Git.
    public_manifest = {
        **manifest,
        "records": [
            {k: r[k] for k in ["path", "label", "split", "group", "pcm_sha256", "file_sha256"]}
            for r in records
        ],
    }
    (args.output / "data-provenance.json").write_text(json.dumps(public_manifest, indent=2))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
