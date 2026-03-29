from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TimelineScene:
    id: str
    scene_role: str
    type: str
    path: str
    start: float
    end: float
    duration: float
    text: str | None = None
    transition: str | None = None
    mood: str | None = None
    camera: str | None = None
    visual_intent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Timeline:
    format: str
    width: int
    height: int
    fps: int
    audio_path: str
    subtitle_path: str
    total_duration: float
    scenes: list[TimelineScene]

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "audio_path": self.audio_path,
            "subtitle_path": self.subtitle_path,
            "total_duration": self.total_duration,
            "scenes": [scene.to_dict() for scene in self.scenes],
        }
