import json
import os
from src.image_registry import load_images
from src.audio_utils import get_audio_duration

def build_timeline(job_root):
    manifest_path = os.path.join(job_root, "visual_manifest.json")
    images_path = os.path.join(job_root, "images")
    audio_path = os.path.join(job_root, "audio", "narration.wav")

    with open(manifest_path) as f:
        manifest = json.load(f)

    scenes = manifest["scene_plan"]
    images = load_images(images_path)
    duration = get_audio_duration(audio_path)

    timeline = {
        "duration": duration,
        "scenes": []
    }

    for i, scene in enumerate(scenes):
        image = images[i] if i < len(images) else images[-1]

        timeline["scenes"].append({
            "scene_id": scene["scene_id"],
            "start": scene["start_sec"],
            "end": scene["end_sec"],
            "main_image": image
        })

    output_path = os.path.join(job_root, "timeline", "timeline_final.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(timeline, f, indent=2)

    return output_path
