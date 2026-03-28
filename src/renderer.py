import json
import os
from moviepy.editor import concatenate_videoclips
from src.moviepy_utils import create_clip
from src.ffmpeg_utils import add_audio, add_subtitles

def render(job_root):
    timeline_path = os.path.join(job_root, "timeline", "timeline_final.json")
    audio_path = os.path.join(job_root, "audio", "narration.wav")
    srt_path = os.path.join(job_root, "subtitles", "narration.srt")

    with open(timeline_path) as f:
        timeline = json.load(f)

    clips = []

    for scene in timeline["scenes"]:
        duration = scene["end"] - scene["start"]
        clip = create_clip(scene["main_image"], duration)
        clips.append(clip)

    video = concatenate_videoclips(clips)

    output_base = os.path.join(job_root, "output", "video_base.mp4")
    os.makedirs(os.path.dirname(output_base), exist_ok=True)

    video.write_videofile(output_base, fps=30)

    video_audio = os.path.join(job_root, "output", "video_with_audio.mp4")
    add_audio(output_base, audio_path, video_audio)

    final = os.path.join(job_root, "output", "video_final.mp4")
    add_subtitles(video_audio, srt_path, final)

    return final
