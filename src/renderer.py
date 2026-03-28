import json

from moviepy.editor import concatenate_videoclips

from src.ffmpeg_utils import add_audio, add_subtitles
from src.job_paths import coerce_job_paths
from src.moviepy_utils import create_clip


def _require_file(path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")


def render(job_root) -> str:
    job_paths = coerce_job_paths(job_root)
    timeline_path = job_paths.timeline_path
    audio_path = job_paths.audio_path
    srt_path = job_paths.subtitles_path
    output_base = job_paths.output_base_path
    video_audio = job_paths.output_with_audio_path
    final_output = job_paths.final_output_path

    _require_file(timeline_path, "timeline file")
    _require_file(audio_path, "narration audio")
    _require_file(srt_path, "subtitle file")

    with timeline_path.open("r", encoding="utf-8") as handle:
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

        job_paths.output_dir.mkdir(parents=True, exist_ok=True)

        video = concatenate_videoclips(clips, method="compose")
        video.write_videofile(str(output_base), fps=30)

        add_audio(str(output_base), str(audio_path), str(video_audio))
        add_subtitles(str(video_audio), str(srt_path), str(final_output))
    finally:
        if video is not None:
            video.close()

        for clip in clips:
            clip.close()

    return str(final_output)
