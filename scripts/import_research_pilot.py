"""Acquire a pinned research-only real-audio pilot; never redistribute audio in Git."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf
from huggingface_hub import hf_hub_download

from car_fault_detection.data.manifest import validate_manifest

REPO = "rayyyyy007/kwerimoto-engine-sounds"
REVISION = "0335c63789e2ceedfbf521983db59642420864c2"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/research/kwerimoto"))
    parser.add_argument("--allow-research-only", action="store_true")
    parser.add_argument("--train-per-class", type=int, default=20)
    parser.add_argument("--eval-per-class", type=int, default=6)
    args = parser.parse_args()
    if args.train_per_class < 1 or args.eval_per_class < 1:
        parser.error("Per-class limits must be positive")
    if not args.allow_research_only:
        parser.error(
            "Source permits research/education; pass --allow-research-only for a non-release pilot"
        )
    source = hf_hub_download(REPO, "manifest.csv", repo_type="dataset", revision=REVISION)
    with open(source) as handle:
        rows = list(csv.DictReader(handle))
    selected = []
    counts = Counter()
    limits = {
        "train": args.train_per_class,
        "validation": args.eval_per_class,
        "test": args.eval_per_class,
    }
    for row in sorted(rows, key=lambda row: row["file_name"]):
        if row["split"] not in limits or row["synthetic"].lower() == "true":
            continue
        if row["source_dataset"] == "audioset" and row["vehicle_tag"] != "car":
            continue
        if float(row["duration_s"]) < 1:
            continue
        key = (row["split"], row["label"])
        if counts[key] < limits[row["split"]]:
            counts[key] += 1
            selected.append(row)
    args.output.mkdir(parents=True, exist_ok=True)

    def fetch(row):
        relative = Path(row["file_name"])
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "prepared":
            raise ValueError("Invalid source path")
        source_path = hf_hub_download(
            REPO, row["file_name"], repo_type="dataset", revision=REVISION
        )
        audio, rate = sf.read(source_path, dtype="float32")
        if rate != 16000 or audio.ndim != 1 or len(audio) < 16000 or len(audio) > 160001:
            raise ValueError("Unexpected source audio format")
        if not np.isfinite(audio).all() or np.max(np.abs(audio)) == 0:
            raise ValueError("Invalid/silent recording")
        destination = args.output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = Path(source_path).read_bytes()
        destination.write_bytes(content)
        return {
            "path": relative.as_posix(),
            "label": row["label"],
            "split": row["split"],
            "group": row["group"],
            "source_dataset": row["source_dataset"],
            "file_sha256": hashlib.sha256(content).hexdigest(),
            "pcm_sha256": hashlib.sha256(audio.tobytes()).hexdigest(),
            "duration_s": len(audio) / rate,
        }

    records = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for record in pool.map(fetch, selected):
            records.append(record)
            print(f"Downloaded {len(records)}/{len(selected)}", flush=True)
    validate_manifest(records)
    provenance = {
        "dataset": REPO,
        "revision": REVISION,
        "release_allowed": False,
        "usage": "research_education_only_original_source_rights_unverified",
        "selection": "real clips only; AudioSet restricted to explicit car tags; deterministic per-split class caps; no real_test use",
        "counts": {f"{split}/{label}": count for (split, label), count in counts.items()},
        "limitations": [
            "No Ethiopian vehicle validation",
            "No mechanic-confirmed ground truth",
            "Source/acoustic confounding",
            "Small pilot, not a production benchmark",
        ],
        "records": records,
    }
    (args.output / "manifest.json").write_text(json.dumps(provenance, indent=2))
    print(
        json.dumps({key: value for key, value in provenance.items() if key != "records"}, indent=2)
    )


if __name__ == "__main__":
    main()
