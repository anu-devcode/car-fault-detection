import pytest

from car_fault_detection.data.manifest import validate_manifest


def sample():
    return [
        {"split": split, "label": label, "group": split + label, "pcm_sha256": split + label}
        for split in ["train", "validation", "test"]
        for label in ["healthy", "knock"]
    ]


def test_source_and_decoded_duplicate_leakage_is_blocked():
    for key in ["group", "pcm_sha256"]:
        rows = sample()
        rows[-1][key] = rows[0][key]
        with pytest.raises(ValueError, match="crosses split"):
            validate_manifest(rows)


def test_missing_class_or_source_metadata_blocks_training():
    rows = sample()
    validate_manifest(rows)
    with pytest.raises(ValueError, match="coverage"):
        validate_manifest(rows[:-1])
    rows[0]["group"] = ""
    with pytest.raises(ValueError, match="required"):
        validate_manifest(rows)
