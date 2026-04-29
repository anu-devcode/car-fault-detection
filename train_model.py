"""Step 3: train baseline model from extracted feature dataset."""

from pathlib import Path


FEATURE_FILE = Path("data") / "processed" / "features.csv"


def main() -> None:
    if not FEATURE_FILE.exists():
        print("Missing data/processed/features.csv.")
        print("Run feature_extraction.py first.")
        return

    print("Training entry point ready.")
    print("Next: load features.csv and train baseline RandomForest and SVM.")


if __name__ == "__main__":
    main()
