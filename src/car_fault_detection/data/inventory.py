"""Read-only inventory of the project's actual audio dataset layout."""

import argparse
import json
from collections import Counter
from pathlib import Path

from car_fault_detection import config

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".webm", ".opus"}


def inspect_dataset(directory: Path) -> dict:
    if directory.exists() and not directory.is_dir():
        raise ValueError(f"Not a dataset directory: {directory}")
    counts = Counter()
    splits = Counter()
    empty = []
    records = []
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            continue
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        if path.stat().st_size == 0:
            empty.append(relative.as_posix())
            continue
        split = relative.parts[0] if relative.parts[0] in {"train", "test", "val"} else "unsplit"
        # Existing training code uses the immediate parent directory as the source label.
        label = path.parent.name if len(relative.parts) > 1 else "unlabeled"
        counts[label] += 1
        splits[split] += 1
        records.append({"path": relative.as_posix(), "label": label, "split": split})
    return {
        "dataset_dir": str(directory),
        "audio_files": len(records),
        "class_counts": dict(sorted(counts.items())),
        "split_counts": dict(sorted(splits.items())),
        "empty_files": empty,
        "records": records,
        "audio_content_validated": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(config.DATASET_DIR))
    args = parser.parse_args(argv)
    try:
        inventory = inspect_dataset(args.directory)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(json.dumps(inventory, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
