from __future__ import annotations

from pathlib import Path

from PIL import Image
from moviepy.editor import ImageClip, VideoFileClip, concatenate_videoclips, vfx

from src.ffmpeg_utils import run_ffprobe_json

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS


def get_audio_duration(path: Path) -> float:
    payload = run_ffprobe_json(
        [
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ]
    )
    duration = float(payload["format"]["duration"])
    if duration <= 0:
        raise ValueError(f"Audio file has invalid duration: {path}")
    return duration


def get_video_duration(path: Path) -> float:
    payload = run_ffprobe_json(
        [
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ]
    )
    duration = float(payload["format"]["duration"])
    if duration <= 0:
        raise ValueError(f"Video file has invalid duration: {path}")
    return duration


def _cover_resize(clip, width: int, height: int):
    scale = max(width / clip.w, height / clip.h)
    resized = clip.resize(scale)
    x_center = resized.w / 2
    y_center = resized.h / 2
    return resized.crop(
        x_center=x_center,
        y_center=y_center,
        width=width,
        height=height,
    )


def create_vertical_image_clip(asset_path: Path, duration: float, width: int, height: int, fps: int):
    if duration <= 0:
        raise ValueError(f"Clip duration must be greater than zero. Received {duration}.")

    clip = ImageClip(str(asset_path)).set_duration(duration).set_fps(fps)
    return _cover_resize(clip, width=width, height=height)


def create_vertical_video_clip(asset_path: Path, duration: float, width: int, height: int, fps: int):
    if duration <= 0:
        raise ValueError(f"Clip duration must be greater than zero. Received {duration}.")

    clip = VideoFileClip(str(asset_path), audio=False)
    if clip.duration >= duration:
        trimmed = clip.subclip(0, duration)
    else:
        trimmed = clip.fx(vfx.loop, duration=duration)

    return _cover_resize(trimmed.set_fps(fps), width=width, height=height)


def create_clip(asset_path: Path, asset_type: str, duration: float, width: int, height: int, fps: int):
    if asset_type == "image":
        return create_vertical_image_clip(asset_path, duration, width, height, fps)

    if asset_type == "video":
        return create_vertical_video_clip(asset_path, duration, width, height, fps)

    raise ValueError(f"Unsupported asset_type '{asset_type}' for asset '{asset_path}'.")


def concatenate_clips(clips: list, width: int, height: int, fps: int):
    if not clips:
        raise ValueError("No clips were provided for concatenation.")

    video = concatenate_videoclips(clips, method="compose")
    return video.set_fps(fps)
