from moviepy.editor import ImageClip, VideoFileClip, vfx


def create_clip(asset_path: str, asset_type: str, duration: float):
    if duration <= 0:
        raise ValueError(f"Clip duration must be greater than zero. Received {duration}.")

    if asset_type == "image":
        return ImageClip(asset_path).set_duration(duration)

    if asset_type == "video":
        clip = VideoFileClip(asset_path)

        if clip.duration >= duration:
            return clip.subclip(0, duration)

        try:
            return clip.fx(vfx.loop, duration=duration)
        except Exception:
            return clip.set_duration(duration)

    raise ValueError(f"Unsupported asset_type '{asset_type}' for asset '{asset_path}'.")
