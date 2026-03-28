from dataclasses import dataclass
from typing import List

@dataclass
class Scene:
    scene_id: str
    start: float
    end: float
    main_image: str

@dataclass
class Timeline:
    duration: float
    scenes: List[Scene]
