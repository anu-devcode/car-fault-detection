"""Step 4: evaluate trained model metrics."""

from pathlib import Path


MODEL_FILE = Path("data") / "processed" / "model.joblib"


def main() -> None:
    if not MODEL_FILE.exists():
        print("Missing data/processed/model.joblib.")
        print("Run train_model.py first.")
        return

    print("Evaluation entry point ready.")
    print("Next: report accuracy, confusion matrix, precision, and recall.")


if __name__ == "__main__":
    main()
