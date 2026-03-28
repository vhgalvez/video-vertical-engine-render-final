from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class Scene:
    scene_id: str
    start: float
    end: float
    asset_type: str
    asset_path: str
    fallback_image: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Timeline:
    duration: float
    scenes: List[Scene]

    def to_dict(self) -> dict:
        return {
            "duration": self.duration,
            "scenes": [scene.to_dict() for scene in self.scenes],
        }
