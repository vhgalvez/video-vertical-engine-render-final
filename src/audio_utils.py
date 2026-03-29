from __future__ import annotations

from pathlib import Path

from src.moviepy_utils import get_audio_duration


def get_audio_duration_seconds(path: str | Path) -> float:
    return get_audio_duration(Path(path))
