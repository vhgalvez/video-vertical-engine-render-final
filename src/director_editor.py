import json
from pathlib import Path

from src.asset_registry import list_assets_in_order, load_asset_indexes, resolve_asset_for_scene
from src.audio_utils import get_audio_duration
from src.job_paths import coerce_job_paths
from src.schemas import Scene, Timeline


def _load_manifest(manifest_path: Path) -> dict:
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    scene_plan = manifest.get("scene_plan")
    if not scene_plan:
        raise ValueError("visual_manifest.json must include a non-empty 'scene_plan'.")

    return manifest


def _validate_audio(audio_path: Path) -> None:
    if not audio_path.is_file():
        raise FileNotFoundError(f"Missing narration audio: {audio_path}")


def _build_scene(scene_data: dict, position: int, asset_indexes: dict, ordered_assets: list) -> Scene:
    scene_id = scene_data.get("scene_id")
    start = scene_data.get("start_sec")
    end = scene_data.get("end_sec")

    if scene_id in (None, ""):
        raise ValueError(f"Scene at index {position} is missing 'scene_id'.")
    if start is None:
        raise ValueError(f"Scene '{scene_id}' is missing 'start_sec'.")
    if end is None:
        raise ValueError(f"Scene '{scene_id}' is missing 'end_sec'.")
    if start < 0:
        raise ValueError(f"Scene '{scene_id}' has invalid start_sec={start}. Expected start_sec >= 0.")
    if end <= start:
        raise ValueError(
            f"Scene '{scene_id}' has invalid range start_sec={start}, end_sec={end}. Expected end_sec > start_sec."
        )

    asset = resolve_asset_for_scene(
        scene_id=scene_id,
        asset_indexes=asset_indexes,
        ordered_assets=ordered_assets,
        position=position,
    )
    if asset is None:
        raise ValueError(
            f"Could not resolve any visual asset for scene '{scene_id}' at position {position}."
        )

    fallback_image = None
    if asset["used_fallback"] and asset["asset_type"] == "image":
        fallback_image = asset["asset_path"]

    return Scene(
        scene_id=scene_id,
        start=float(start),
        end=float(end),
        asset_type=asset["asset_type"],
        asset_path=asset["asset_path"],
        fallback_image=fallback_image,
    )


def build_timeline(job_root) -> str:
    job_paths = coerce_job_paths(job_root)
    manifest_path = job_paths.require_manifest_path()
    audio_path = job_paths.audio_path
    output_path = job_paths.timeline_path

    manifest = _load_manifest(manifest_path)
    _validate_audio(audio_path)

    asset_indexes = load_asset_indexes(job_paths)
    ordered_assets = list_assets_in_order(asset_indexes)
    if not ordered_assets:
        raise ValueError("No visual assets found in 'images/' or 'videos/'.")

    duration = float(get_audio_duration(audio_path))
    scenes = [
        _build_scene(scene_data, position, asset_indexes, ordered_assets)
        for position, scene_data in enumerate(manifest["scene_plan"])
    ]

    timeline = Timeline(duration=duration, scenes=scenes)
    job_paths.timeline_dir.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(timeline.to_dict(), handle, indent=2)

    return str(output_path)
