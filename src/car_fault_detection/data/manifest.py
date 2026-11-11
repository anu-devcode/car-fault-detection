"""Validate recording-level separation before any transfer-learning run."""


def validate_manifest(records: list[dict]) -> None:
    if not records:
        raise ValueError("No recordings selected")
    groups = {}
    hashes = {}
    for row in records:
        split = row.get("split")
        if split not in {"train", "validation", "test"}:
            raise ValueError(f"Invalid training split: {split}")
        if not row.get("group") or not row.get("pcm_sha256"):
            raise ValueError("Recording group and decoded-audio hash are required")
        for value, registry in [(row["group"], groups), (row["pcm_sha256"], hashes)]:
            if value in registry and registry[value] != split:
                raise ValueError("Recording group or duplicate audio crosses split boundaries")
            registry[value] = split
    classes = {row["label"] for row in records if row["split"] == "train"}
    if len(classes) < 2:
        raise ValueError("At least two training classes are required")
    for split in ("validation", "test"):
        if {row["label"] for row in records if row["split"] == split} != classes:
            raise ValueError(f"Class coverage differs in {split}")
