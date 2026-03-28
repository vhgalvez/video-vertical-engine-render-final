import os

def add_audio(video_path, audio_path, output_path):
    cmd = f"ffmpeg -y -i {video_path} -i {audio_path} -c:v copy -c:a aac -shortest {output_path}"
    os.system(cmd)

def add_subtitles(video_path, srt_path, output_path):
    cmd = f"ffmpeg -y -i {video_path} -vf subtitles={srt_path} {output_path}"
    os.system(cmd)
