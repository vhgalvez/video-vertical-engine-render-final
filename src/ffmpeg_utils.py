from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def run_ffprobe_json(arguments: list[str]) -> dict[str, Any]:
    completed = run_command(["ffprobe", *arguments])
    stdout = completed.stdout.strip()
    if not stdout:
        return {}
    return json.loads(stdout)


def ffmpeg_subtitle_filter_path(path: Path) -> str:
    value = path.resolve().as_posix()
    value = value.replace("\\", "/")
    value = value.replace(":", "\\:")
    value = value.replace("'", r"\'")
    value = value.replace("[", r"\[")
    value = value.replace("]", r"\]")
    value = value.replace(",", r"\,")
    return value


def add_audio(video_path: Path, audio_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-filter_complex",
            "[1:a]apad[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_path),
        ]
    )


def add_subtitles(video_path: Path, srt_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subtitle_filter = f"subtitles='{ffmpeg_subtitle_filter_path(srt_path)}'"
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            str(output_path),
        ]
    )
