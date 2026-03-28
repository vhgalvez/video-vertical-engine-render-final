import logging
import os
from typing import Dict, List, Optional


LOGGER = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def _safe_listdir(path: str) -> List[str]:
    if not os.path.isdir(path):
        return []
    return sorted(os.listdir(path))


def _build_index(directory: str, valid_extensions: set, asset_kind: str) -> Dict[str, str]:
    index: Dict[str, str] = {}

    for entry in _safe_listdir(directory):
        full_path = os.path.join(directory, entry)
        if not os.path.isfile(full_path):
            continue

        stem, extension = os.path.splitext(entry)
        if extension.lower() not in valid_extensions:
            continue

        if stem in index:
            raise ValueError(
                f"Duplicate {asset_kind} asset stem '{stem}' found in '{directory}'. "
                "Use unique filenames per scene."
            )

        index[stem] = full_path

    return index


def load_asset_indexes(job_root: str) -> Dict[str, Dict[str, str]]:
    images_dir = os.path.join(job_root, "images")
    videos_dir = os.path.join(job_root, "videos")

    images = _build_index(images_dir, IMAGE_EXTENSIONS, "image")
    videos = _build_index(videos_dir, VIDEO_EXTENSIONS, "video")

    return {
        "images": images,
        "videos": videos,
    }


def list_assets_in_order(asset_indexes: Dict[str, Dict[str, str]]) -> List[dict]:
    assets: List[dict] = []

    for stem, path in asset_indexes.get("images", {}).items():
        assets.append(
            {
                "scene_id": stem,
                "asset_type": "image",
                "asset_path": path,
            }
        )

    for stem, path in asset_indexes.get("videos", {}).items():
        assets.append(
            {
                "scene_id": stem,
                "asset_type": "video",
                "asset_path": path,
            }
        )

    assets.sort(key=lambda asset: (asset["scene_id"], 0 if asset["asset_type"] == "video" else 1))
    return assets


def resolve_asset_for_scene(
    scene_id: str,
    asset_indexes: Dict[str, Dict[str, str]],
    ordered_assets: Optional[List[dict]] = None,
    position: Optional[int] = None,
) -> Optional[dict]:
    videos = asset_indexes.get("videos", {})
    images = asset_indexes.get("images", {})

    if scene_id in videos:
        return {
            "scene_id": scene_id,
            "asset_type": "video",
            "asset_path": videos[scene_id],
            "used_fallback": False,
        }

    if scene_id in images:
        return {
            "scene_id": scene_id,
            "asset_type": "image",
            "asset_path": images[scene_id],
            "used_fallback": False,
        }

    if ordered_assets is None:
        ordered_assets = list_assets_in_order(asset_indexes)

    if position is None or position < 0 or position >= len(ordered_assets):
        return None

    fallback_asset = ordered_assets[position]
    LOGGER.warning(
        "Scene '%s' has no direct asset match. Using positional fallback '%s'.",
        scene_id,
        fallback_asset["asset_path"],
    )
    return {
        "scene_id": fallback_asset["scene_id"],
        "asset_type": fallback_asset["asset_type"],
        "asset_path": fallback_asset["asset_path"],
        "used_fallback": True,
    }
