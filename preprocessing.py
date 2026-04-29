"""Step 1: validate raw dataset layout before preprocessing."""

from pathlib import Path


RAW_DIR = Path("data") / "raw"
PROCESSED_DIR = Path("data") / "processed"


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not RAW_DIR.exists():
        print("Missing data/raw. Add your cloned dataset first.")
        return

    labels = sorted([p.name for p in RAW_DIR.iterdir() if p.is_dir()])
    if not labels:
        print("No class folders found in data/raw.")
        return

    print("Dataset folders detected:")
    for label in labels:
        print(f"- {label}")

    print("Preprocessing step ready. Next, implement audio cleaning/normalization.")


if __name__ == "__main__":
    main()
