from moviepy.editor import ImageClip

def create_clip(image_path, duration):
    return ImageClip(image_path).set_duration(duration)
