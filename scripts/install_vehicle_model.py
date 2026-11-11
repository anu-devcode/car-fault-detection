"""Install a revision-pinned optional photo model locally, outside Git."""

import hashlib
import json
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO = "Jordo23/vehicle-classifier"
REVISION = "7a0a0ee5584202b5eba858cf7464f5ca6b7341b3"

if __name__ == "__main__":
    destination = Path("models/vehicle-photo")
    destination.mkdir(parents=True, exist_ok=True)
    checksums = {}
    for filename in ["vehicle_classifier.pth", "class_mapping.csv"]:
        path = hf_hub_download(REPO, filename, revision=REVISION)
        shutil.copyfile(path, destination / filename)
        checksums[filename] = hashlib.sha256((destination / filename).read_bytes()).hexdigest()
    provenance = {
        "repo": REPO,
        "revision": REVISION,
        "sha256": checksums,
        "model_card_license": "MIT",
        "dataset_rights": "VMMRdb rights require separate review",
        "release_allowed": False,
    }
    (destination / "provenance.json").write_text(json.dumps(provenance, indent=2))
    print("Installed. Set VISION_MODEL_DIR to", destination.resolve())
