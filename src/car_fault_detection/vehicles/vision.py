"""Optional pretrained vehicle-photo classifier; never verifies a vehicle identity."""

import csv
import hashlib
import io
import json
import re
from pathlib import Path


class VehicleRecognizer:
    def __init__(self, directory):
        import timm
        import torch
        from torchvision import transforms

        directory = Path(directory)
        metadata = json.loads((directory / "provenance.json").read_text())
        for filename in ["vehicle_classifier.pth", "class_mapping.csv"]:
            if (
                hashlib.sha256((directory / filename).read_bytes()).hexdigest()
                != metadata["sha256"][filename]
            ):
                raise ValueError("Photo checkpoint content differs from its installed provenance")
        checkpoint = torch.load(
            directory / "vehicle_classifier.pth", map_location="cpu", weights_only=True
        )
        with (directory / "class_mapping.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        self.labels = {int(row["global_class_id"]): row for row in rows}
        count = checkpoint["num_classes"]
        if set(self.labels) != set(range(count)):
            raise ValueError("Photo label mapping is incomplete")
        if any(
            self.labels[index]["class_name"] != checkpoint["class_mapping"][index]
            for index in range(count)
        ):
            raise ValueError("Photo checkpoint and label mapping disagree")
        self.model = timm.create_model("efficientnet_b4", pretrained=False, num_classes=count)
        self.model.load_state_dict(checkpoint["model_state"], strict=True)
        self.model.eval()
        self.transform = transforms.Compose(
            [
                transforms.Resize((380, 380)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        self.revision = metadata["revision"]

    def predict(self, content):
        import torch
        from PIL import Image, ImageOps, UnidentifiedImageError

        try:
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Use a JPEG, PNG or WEBP photograph")
                if min(image.size) < 80 or image.width * image.height > 16_000_000:
                    raise ValueError(
                        "Photo dimensions must be at least 80px and at most 16 megapixels"
                    )
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                tensor = self.transform(ImageOps.exif_transpose(image).convert("RGB"))[None]
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise ValueError("Unable to decode photograph") from exc
        with torch.inference_mode():
            scores, indices = self.model(tensor).softmax(1).topk(5)
        candidates = []
        for score, index in zip(scores[0].tolist(), indices[0].tolist()):
            row = self.labels[index]
            match = re.search(r"\b(\d{4})$", row["class_name"])
            candidates.append(
                {
                    "label": row["class_name"],
                    "make": row["make"],
                    "model": row["model"],
                    "year_candidate": int(match.group(1)) if match else None,
                    "confidence": score,
                }
            )
        return {
            "status": "candidate_matches_only",
            "confirmation_required": True,
            "candidates": candidates,
            "model_revision": self.revision,
            "notice": "These are possible matches, not verified identity. Non-car photos or unsupported models can still produce confident wrong matches. Confirm using vehicle documents; engine, trim, VIN and history are unknown.",
            "coverage": "8,949 published make/model/year labels; not validated for Ethiopia or every car type",
        }
