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


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _validate_scene_plan(scene_plan: Any) -> tuple[list[dict[str, Any]], float]:
    if not isinstance(scene_plan, list) or not scene_plan:
        raise ValueError("visual_manifest.scene_plan must be a non-empty list.")

    normalized_scenes: list[dict[str, Any]] = []
    seen_scene_ids: set[str] = set()
    previous_end = 0.0

    for index, raw_scene in enumerate(scene_plan, start=1):
        if not isinstance(raw_scene, dict):
            raise ValueError(f"scene_plan entry #{index} must be an object.")

        scene_id = str(raw_scene.get("scene_id", "")).strip()
        if not scene_id:
            raise ValueError(f"scene_plan entry #{index} is missing 'scene_id'.")
        if scene_id in seen_scene_ids:
            raise ValueError(f"scene_plan contains duplicate scene_id '{scene_id}'.")
        seen_scene_ids.add(scene_id)

        start = round(_coerce_float(raw_scene.get("start_sec"), f"{scene_id}.start_sec"), 3)
        end = round(_coerce_float(raw_scene.get("end_sec"), f"{scene_id}.end_sec"), 3)
        if start < 0:
            raise ValueError(f"Scene '{scene_id}' has invalid start_sec={start}. Expected start_sec >= 0.")
        if end <= start:
            raise ValueError(f"Scene '{scene_id}' has invalid range start_sec={start}, end_sec={end}.")

        if index == 1 and start != 0:
            raise ValueError(
                f"scene_plan must start at 0.0 seconds for the first scene. "
                f"Received start_sec={start} for '{scene_id}'."
            )

        if abs(start - previous_end) > 0.05:
            raise ValueError(
                f"scene_plan is not contiguous before '{scene_id}'. "
                f"Expected start_sec={previous_end:.3f}, received {start:.3f}."
            )

        previous_end = end
        normalized_scenes.append(raw_scene)

    return normalized_scenes, previous_end


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
        text=_optional_str(scene_data.get("text")),
        transition=_optional_str(scene_data.get("transition")),
        mood=_optional_str(scene_data.get("mood")),
        camera=_optional_str(scene_data.get("camera")),
        visual_intent=_optional_str(scene_data.get("visual_intent")),
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
                text=None,
                transition=None,
                mood=None,
                camera=None,
                visual_intent=None,
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

    audio_duration = round(get_audio_duration(audio_path), 3)
    LOGGER.info("Duracion del audio: %.3f segundos", audio_duration)

    scene_plan = manifest_data.get("scene_plan")
    registry = load_asset_registry(job_paths)

    if scene_plan:
        scene_plan, timeline_total_duration = _validate_scene_plan(scene_plan)
        LOGGER.info("scene_plan cargado: %s escenas", len(scene_plan))
        if abs(timeline_total_duration - audio_duration) > 0.25:
            LOGGER.warning(
                "Desajuste entre scene_plan y audio. Se preserva scene_plan como fuente de verdad. "
                "timeline_end=%.3f audio_duration=%.3f",
                timeline_total_duration,
                audio_duration,
            )
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
                "Asset encontrado por scene_id %s: %s (%s)",
                asset.scene_id,
                job_paths.relative_to_job(asset.path),
                asset.type,
            )

        scenes = [_build_scene_from_plan(scene_data, asset_path_by_scene) for scene_data in scene_plan]
    else:
        LOGGER.warning(
            "scene_plan no detectado. Se activa fallback tecnico por assets + duracion de audio. "
            "Este modo no preserva direccion editorial upstream."
        )
        timeline_total_duration = audio_duration
        scenes = _build_fallback_scenes(job_paths, audio_duration)
        for scene in scenes:
            LOGGER.info("Asset fallback para %s: %s (%s)", scene.id, scene.path, scene.type)

    timeline = Timeline(
        format=render_format,
        width=VERTICAL_WIDTH,
        height=VERTICAL_HEIGHT,
        fps=VERTICAL_FPS,
        audio_path=job_paths.relative_to_job(audio_path),
        subtitle_path=job_paths.relative_to_job(subtitle_path),
        total_duration=round(timeline_total_duration, 3),
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
