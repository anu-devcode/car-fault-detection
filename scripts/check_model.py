"""Validate the configured checkpoint; no inference accuracy is inferred here."""

import logging

from car_fault_detection.api.app import load_detector

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        detector = load_detector()
    except (OSError, RuntimeError, ValueError) as exc:
        logging.error("Checkpoint validation failed: %s", exc)
        raise SystemExit(1) from exc
    print("Checkpoint matches the current architecture. Classes:", list(detector.classes))
