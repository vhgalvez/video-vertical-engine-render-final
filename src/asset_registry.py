from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.job_paths import JobPaths, coerce_job_paths


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm")


@dataclass(frozen=True)
class ResolvedAsset:
    scene_id: str
    type: str
    path: Path

    def to_job_relative_dict(self, job_paths: JobPaths) -> dict[str, str]:
        return {
            "scene_id": self.scene_id,
            "type": self.type,
            "path": job_paths.relative_to_job(self.path),
        }


def _build_extension_index(directory: Path, extensions: Iterable[str], asset_type: str) -> dict[str, Path]:
    index: dict[str, Path] = {}
    if not directory.is_dir():
        return index

    allowed_extensions = {extension.lower() for extension in extensions}
    for entry in sorted(directory.iterdir(), key=lambda current: current.name.lower()):
        if not entry.is_file():
            continue

        suffix = entry.suffix.lower()
        if suffix not in allowed_extensions:
            continue

        stem = entry.stem
        if stem in index:
            raise ValueError(
                f"Duplicate {asset_type} asset for scene '{stem}' in '{directory}'. "
                "Keep a single file per scene_id and asset type."
            )

        index[stem] = entry.resolve()

    return index


def load_asset_registry(job_root: JobPaths | str | Path) -> dict[str, dict[str, Path]]:
    job_paths = coerce_job_paths(job_root)
    return {
        "images": _build_extension_index(job_paths.images_dir, IMAGE_EXTENSIONS, "image"),
        "videos": _build_extension_index(job_paths.videos_dir, VIDEO_EXTENSIONS, "video"),
    }


def discover_assets(job_root: JobPaths | str | Path) -> list[ResolvedAsset]:
    job_paths = coerce_job_paths(job_root)
    registry = load_asset_registry(job_paths)
    scene_ids = sorted(set(registry["images"]) | set(registry["videos"]))

    assets: list[ResolvedAsset] = []
    for scene_id in scene_ids:
        assets.append(resolve_asset_for_scene(scene_id=scene_id, registry=registry))

    return assets


def resolve_asset_for_scene(scene_id: str, registry: dict[str, dict[str, Path]]) -> ResolvedAsset:
    videos = registry.get("videos", {})
    images = registry.get("images", {})

    if scene_id in videos:
        return ResolvedAsset(scene_id=scene_id, type="video", path=videos[scene_id])

    if scene_id in images:
        return ResolvedAsset(scene_id=scene_id, type="image", path=images[scene_id])

    searched_names = ", ".join(
        [f"{scene_id}{extension}" for extension in VIDEO_EXTENSIONS + IMAGE_EXTENSIONS]
    )
    raise FileNotFoundError(
        f"Missing visual asset for scene '{scene_id}'. Expected one of: {searched_names}"
    )


def validate_scene_assets(scene_ids: Iterable[str], registry: dict[str, dict[str, Path]]) -> list[ResolvedAsset]:
    resolved_assets: list[ResolvedAsset] = []
    missing_scene_ids: list[str] = []

    for scene_id in scene_ids:
        try:
            resolved_assets.append(resolve_asset_for_scene(scene_id=scene_id, registry=registry))
        except FileNotFoundError:
            missing_scene_ids.append(scene_id)

    if missing_scene_ids:
        missing_details = "; ".join(
            f"{scene_id}: "
            + ", ".join(f"{scene_id}{extension}" for extension in VIDEO_EXTENSIONS + IMAGE_EXTENSIONS)
            for scene_id in missing_scene_ids
        )
        raise FileNotFoundError(
            "Missing visual assets for scene_plan scenes. "
            f"Expected one file per scene_id with video priority over image. Missing: {missing_details}"
        )

    return resolved_assets
