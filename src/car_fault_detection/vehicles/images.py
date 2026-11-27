"""Decode supported single-frame photographs before running vision models."""

import io


def decode_photo(content: bytes):
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Use a JPEG, PNG or WEBP photograph.")
            if min(image.size) < 80 or image.width * image.height > 16_000_000:
                raise ValueError(
                    "Use a photo at least 80 pixels per side and at most 16 megapixels."
                )
            if getattr(image, "is_animated", False):
                raise ValueError("Use a single photograph rather than an animation.")
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            return ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ValueError("Unable to decode photograph.") from exc
