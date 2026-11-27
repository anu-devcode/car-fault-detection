"""Shared one-second windows for recording-level training and research inference."""


def recording_windows(audio, sample_rate: int, count: int):
    if count not in {1, 3}:
        raise ValueError("Supported window counts are one and three")
    if sample_rate <= 0 or len(audio) < sample_rate:
        raise ValueError("Record at least one second of engine audio.")
    last_start = len(audio) - sample_rate
    middle = last_start // 2
    starts = (middle,) if count == 1 else tuple(dict.fromkeys((0, middle, last_start)))
    return [audio[start : start + sample_rate] for start in starts]
