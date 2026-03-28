import json
import os

from moviepy.editor import concatenate_videoclips

from src.ffmpeg_utils import add_audio, add_subtitles
from src.moviepy_utils import create_clip


def _require_file(path: str, label: str) -> None:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing {label}: {path}")


def render(job_root: str) -> str:
    timeline_path = os.path.join(job_root, "timeline", "timeline_final.json")
    audio_path = os.path.join(job_root, "audio", "narration.wav")
    srt_path = os.path.join(job_root, "subtitles", "narration.srt")
    output_base = os.path.join(job_root, "output", "video_base.mp4")
    video_audio = os.path.join(job_root, "output", "video_with_audio.mp4")
    final_output = os.path.join(job_root, "output", "video_final.mp4")

    _require_file(timeline_path, "timeline file")
    _require_file(audio_path, "narration audio")
    _require_file(srt_path, "subtitle file")

    with open(timeline_path, "r", encoding="utf-8") as handle:
        timeline = json.load(handle)

    clips = []
    video = None

    try:
        scenes = timeline.get("scenes", [])
        for scene in scenes:
            duration = float(scene["end"]) - float(scene["start"])
            if duration <= 0:
                raise ValueError(
                    f"Scene '{scene.get('scene_id', 'unknown')}' has invalid duration {duration}."
                )

            clip = create_clip(
                asset_path=scene["asset_path"],
                asset_type=scene["asset_type"],
                duration=duration,
            )
            clips.append(clip)

        if not clips:
            raise ValueError("Timeline does not contain any renderable clips.")

        os.makedirs(os.path.dirname(output_base), exist_ok=True)

        video = concatenate_videoclips(clips, method="compose")
        video.write_videofile(output_base, fps=30)

        add_audio(output_base, audio_path, video_audio)
        add_subtitles(video_audio, srt_path, final_output)
    finally:
        if video is not None:
            video.close()

        for clip in clips:
            clip.close()

    return final_output
