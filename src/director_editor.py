from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.asset_registry import discover_assets, load_asset_registry, validate_scene_assets
from src.job_paths import JobPaths, coerce_job_paths, ensure_supported_format
from src.moviepy_utils import get_audio_duration
from src.schemas import Timeline, TimelineScene


LOGGER = logging.getLogger(__name__)

VERTICAL_WIDTH = 1080
VERTICAL_HEIGHT = 1920
VERTICAL_FPS = 30


@dataclass(frozen=True)
class TimelineBuildResult:
    timeline: Timeline
    timeline_path: Path
    job_data: dict[str, Any]
    status_data: dict[str, Any]
    manifest_data: dict[str, Any]


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _coerce_float(value: Any, label: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {label}: {value!r}") from exc


def _build_scene_from_plan(scene_data: dict[str, Any], asset_path_by_scene: dict[str, str]) -> TimelineScene:
    scene_id = str(scene_data.get("scene_id", "")).strip()
    if not scene_id:
        raise ValueError("Every scene in scene_plan must include a non-empty 'scene_id'.")

    start = _coerce_float(scene_data.get("start_sec"), f"{scene_id}.start_sec")
    end = _coerce_float(scene_data.get("end_sec"), f"{scene_id}.end_sec")
    if start < 0:
        raise ValueError(f"Scene '{scene_id}' has invalid start_sec={start}. Expected start_sec >= 0.")
    if end <= start:
        raise ValueError(f"Scene '{scene_id}' has invalid range start_sec={start}, end_sec={end}.")

    scene_role = str(scene_data.get("scene_role", "")).strip() or "unknown"
    duration = round(end - start, 3)
    asset_path = asset_path_by_scene[scene_id]
    asset_type = "video" if asset_path.startswith("videos/") else "image"

    return TimelineScene(
        id=scene_id,
        scene_role=scene_role,
        type=asset_type,
        path=asset_path,
        start=round(start, 3),
        end=round(end, 3),
        duration=duration,
    )


def _build_fallback_scenes(job_paths: JobPaths, total_duration: float) -> list[TimelineScene]:
    discovered_assets = discover_assets(job_paths)
    if not discovered_assets:
        raise FileNotFoundError(
            f"No visual assets found in '{job_paths.images_dir}' or '{job_paths.videos_dir}'."
        )

    segment_duration = total_duration / len(discovered_assets)
    scenes: list[TimelineScene] = []
    current_start = 0.0

    for index, asset in enumerate(discovered_assets, start=1):
        start = current_start
        end = total_duration if index == len(discovered_assets) else current_start + segment_duration
        current_start = end

        scenes.append(
            TimelineScene(
                id=asset.scene_id,
                scene_role="fallback",
                type=asset.type,
                path=job_paths.relative_to_job(asset.path),
                start=round(start, 3),
                end=round(end, 3),
                duration=round(end - start, 3),
            )
        )

    return scenes


def build_timeline(job_root: JobPaths | str | Path, render_format: str = "vertical") -> TimelineBuildResult:
    job_paths = coerce_job_paths(job_root)
    render_format = ensure_supported_format(render_format)

    job_data = _read_json(job_paths.require_job_file_path(), "job.json")
    status_data = _read_json(job_paths.require_status_path(), "status.json")
    manifest_path = job_paths.require_manifest_path()
    manifest_data = _read_json(manifest_path, "visual_manifest.json")
    audio_path = job_paths.require_audio_path()
    subtitle_path = job_paths.require_subtitles_path()

    LOGGER.info("Job procesado: %s", job_paths.job_id)
    LOGGER.info("visual_manifest cargado: %s", manifest_path)

    total_duration = round(get_audio_duration(audio_path), 3)
    LOGGER.info("Duracion del audio: %.3f segundos", total_duration)

    scene_plan = manifest_data.get("scene_plan")
    registry = load_asset_registry(job_paths)

    if scene_plan:
        LOGGER.info("scene_plan detectado: %s escenas", len(scene_plan))
        resolved_assets = validate_scene_assets(
            scene_ids=[str(scene.get("scene_id", "")).strip() for scene in scene_plan],
            registry=registry,
        )
        asset_path_by_scene = {
            asset.scene_id: job_paths.relative_to_job(asset.path)
            for asset in resolved_assets
        }

        for asset in resolved_assets:
            LOGGER.info(
                "Asset encontrado para %s: %s (%s)",
                asset.scene_id,
                job_paths.relative_to_job(asset.path),
                asset.type,
            )

        scenes = [_build_scene_from_plan(scene_data, asset_path_by_scene) for scene_data in scene_plan]
    else:
        LOGGER.info("scene_plan no detectado. Usando fallback por assets + duracion de audio.")
        scenes = _build_fallback_scenes(job_paths, total_duration)
        for scene in scenes:
            LOGGER.info("Asset fallback para %s: %s (%s)", scene.id, scene.path, scene.type)

    timeline = Timeline(
        format=render_format,
        width=VERTICAL_WIDTH,
        height=VERTICAL_HEIGHT,
        fps=VERTICAL_FPS,
        audio_path=job_paths.relative_to_job(audio_path),
        subtitle_path=job_paths.relative_to_job(subtitle_path),
        total_duration=total_duration,
        scenes=scenes,
    )

    timeline_dir = job_paths.timeline_dir(render_format)
    timeline_dir.mkdir(parents=True, exist_ok=True)
    timeline_path = job_paths.timeline_path(render_format)

    with timeline_path.open("w", encoding="utf-8") as handle:
        json.dump(timeline.to_dict(), handle, indent=2, ensure_ascii=False)

    LOGGER.info("Timeline generado: %s", timeline_path)

    return TimelineBuildResult(
        timeline=timeline,
        timeline_path=timeline_path,
        job_data=job_data,
        status_data=status_data,
        manifest_data=manifest_data,
    )
