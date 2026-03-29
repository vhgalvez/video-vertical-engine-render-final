from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.director_editor import TimelineBuildResult, build_timeline
from src.ffmpeg_utils import add_audio, add_subtitles
from src.job_paths import JobPaths, coerce_job_paths, ensure_supported_format
from src.moviepy_utils import concatenate_clips, create_clip


LOGGER = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_status(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_status(path: Path, status_data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(status_data, handle, indent=2, ensure_ascii=False)


def update_status(job_paths: JobPaths, **updates: Any) -> dict[str, Any]:
    status_path = job_paths.status_path
    status_data = _read_status(status_path)
    status_data.update(updates)
    status_data["updated_at"] = _utc_now_iso()
    _write_status(status_path, status_data)
    return status_data


def _load_timeline_data(build_result: TimelineBuildResult) -> dict[str, Any]:
    with build_result.timeline_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render(job_root: JobPaths | str | Path, render_format: str = "vertical") -> str:
    job_paths = coerce_job_paths(job_root)
    render_format = ensure_supported_format(render_format)

    build_result = build_timeline(job_paths, render_format=render_format)
    update_status(
        job_paths,
        timeline_generated=True,
        render_started=True,
        render_finished=False,
        render_vertical_ready=False,
        last_step="render_vertical_started",
    )

    timeline_data = _load_timeline_data(build_result)
    output_base = job_paths.output_base_path(render_format)
    output_with_audio = job_paths.output_with_audio_path(render_format)
    final_output = job_paths.final_output_path(render_format)
    output_base.parent.mkdir(parents=True, exist_ok=True)

    fps = int(timeline_data["fps"])
    width = int(timeline_data["width"])
    height = int(timeline_data["height"])
    audio_path = job_paths.job_root / timeline_data["audio_path"]
    subtitle_path = job_paths.job_root / timeline_data["subtitle_path"]

    clips = []
    composed_video = None

    try:
        for scene in timeline_data.get("scenes", []):
            scene_id = scene["id"]
            duration = float(scene["duration"])
            if duration <= 0:
                raise ValueError(f"Scene '{scene_id}' has invalid duration {duration}.")

            asset_path = job_paths.job_root / scene["path"]
            clip = create_clip(
                asset_path=asset_path,
                asset_type=scene["type"],
                duration=duration,
                width=width,
                height=height,
                fps=fps,
            )
            clips.append(clip)

        if not clips:
            raise ValueError("Timeline does not contain any renderable scenes.")

        composed_video = concatenate_clips(clips, width=width, height=height, fps=fps)
        composed_video.write_videofile(
            str(output_base),
            fps=fps,
            codec="libx264",
            audio=False,
            preset="medium",
            threads=4,
        )

        add_audio(output_base, audio_path, output_with_audio)
        add_subtitles(output_with_audio, subtitle_path, final_output)
    except Exception:
        update_status(
            job_paths,
            render_started=False,
            render_finished=False,
            render_vertical_ready=False,
            last_step="render_vertical_failed",
        )
        raise
    finally:
        if composed_video is not None:
            composed_video.close()
        for clip in clips:
            clip.close()

    final_relative_path = job_paths.relative_to_job(final_output)
    update_status(
        job_paths,
        render_started=False,
        render_finished=True,
        final_video_path=final_relative_path,
        render_vertical_ready=True,
        last_step="render_vertical_finished",
    )

    LOGGER.info("Ruta final del mp4: %s", final_output)
    return str(final_output)
