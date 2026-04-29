"""Step 2: feature extraction entry point (MFCC + spectrogram + chroma)."""

from pathlib import Path


RAW_DIR = Path("data") / "raw"


def main() -> None:
    if not RAW_DIR.exists():
        print("Missing data/raw. Add raw audio first.")
        return

    audio_files = [p for p in RAW_DIR.rglob("*") if p.is_file() and p.suffix.lower() in {".wav", ".mp3", ".flac", ".ogg", ".m4a"}]
    print(f"Found {len(audio_files)} audio files.")
    print("Next: implement MFCC (required), spectrogram, and chroma extraction.")


if __name__ == "__main__":
    main()
