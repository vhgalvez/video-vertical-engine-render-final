from moviepy.editor import AudioFileClip

def get_audio_duration(path):
    audio = AudioFileClip(path)
    return audio.duration
