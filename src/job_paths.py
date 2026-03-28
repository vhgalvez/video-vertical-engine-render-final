from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


DEFAULT_DATASET_ROOT = "/mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset"
DEFAULT_JOBS_DIRNAME = "jobs"
DEFAULT_MANIFEST_RELATIVE_PATHS = (
    Path("visual_manifest.json"),
    Path("source") / "visual_manifest.json",
)

PathLikeInput = Union[str, os.PathLike[str]]

_WSL_PATH_PATTERN = re.compile(r"^/mnt/([a-zA-Z])/(.*)$")
_WINDOWS_DRIVE_PATTERN = re.compile(r"^([a-zA-Z]):[\\/](.*)$")


def _expand_path(raw_path: PathLikeInput) -> str:
    expanded = os.path.expanduser(os.path.expandvars(os.fspath(raw_path).strip()))
    if not expanded:
        raise ValueError("Expected a non-empty filesystem path.")
    return expanded


def _wsl_to_windows(raw_path: str) -> Optional[str]:
    match = _WSL_PATH_PATTERN.match(raw_path)
    if not match:
        return None

    drive = match.group(1).upper()
    tail = match.group(2).replace("/", "\\")
    return f"{drive}:\\{tail}" if tail else f"{drive}:\\"


def _windows_to_wsl(raw_path: str) -> Optional[str]:
    match = _WINDOWS_DRIVE_PATTERN.match(raw_path)
    if not match:
        return None

    drive = match.group(1).lower()
    tail = match.group(2).replace("\\", "/")
    return f"/mnt/{drive}/{tail}" if tail else f"/mnt/{drive}"


def normalize_path(raw_path: PathLikeInput) -> Path:
    expanded = _expand_path(raw_path)
    candidates = []

    for candidate in (expanded, _wsl_to_windows(expanded), _windows_to_wsl(expanded)):
        if not candidate:
            continue

        path = Path(candidate)
        normalized_key = os.path.normcase(os.path.normpath(str(path)))
        if any(existing[0] == normalized_key for existing in candidates):
            continue
        candidates.append((normalized_key, path))

    for _, candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return candidates[0][1]


def _resolve_existing_dir(raw_path: PathLikeInput, label: str) -> Path:
    path = normalize_path(raw_path)
    if not path.is_dir():
        raise FileNotFoundError(f"Could not find {label}: {path}")
    return path.resolve()


def _resolve_optional_dir(raw_path: Optional[PathLikeInput]) -> Optional[Path]:
    if raw_path in (None, ""):
        return None

    path = normalize_path(raw_path)
    if path.is_dir():
        return path.resolve()
    return None


@dataclass(frozen=True)
class JobPaths:
    dataset_root: Path
    jobs_root: Path
    job_root: Path

    @property
    def manifest_candidates(self) -> tuple[Path, ...]:
        return tuple(self.job_root / relative_path for relative_path in DEFAULT_MANIFEST_RELATIVE_PATHS)

    @property
    def manifest_path(self) -> Path:
        for candidate in self.manifest_candidates:
            if candidate.is_file():
                return candidate
        return self.manifest_candidates[0]

    @property
    def audio_path(self) -> Path:
        return self.job_root / "audio" / "narration.wav"

    @property
    def subtitles_path(self) -> Path:
        return self.job_root / "subtitles" / "narration.srt"

    @property
    def images_dir(self) -> Path:
        return self.job_root / "images"

    @property
    def videos_dir(self) -> Path:
        return self.job_root / "videos"

    @property
    def timeline_dir(self) -> Path:
        return self.job_root / "timeline"

    @property
    def timeline_path(self) -> Path:
        return self.timeline_dir / "timeline_final.json"

    @property
    def output_dir(self) -> Path:
        return self.job_root / "output"

    @property
    def output_base_path(self) -> Path:
        return self.output_dir / "video_base.mp4"

    @property
    def output_with_audio_path(self) -> Path:
        return self.output_dir / "video_with_audio.mp4"

    @property
    def final_output_path(self) -> Path:
        return self.output_dir / "video_final.mp4"

    def require_file(self, path: Path, label: str) -> Path:
        if not path.is_file():
            raise FileNotFoundError(f"Missing {label}: {path}")
        return path

    def require_manifest_path(self) -> Path:
        for candidate in self.manifest_candidates:
            if candidate.is_file():
                return candidate

        candidates = ", ".join(str(path) for path in self.manifest_candidates)
        raise FileNotFoundError(f"Missing visual manifest. Checked: {candidates}")


def resolve_job_paths(
    job_root: Optional[PathLikeInput] = None,
    *,
    job_id: Optional[str] = None,
    dataset_root: Optional[PathLikeInput] = None,
    jobs_root: Optional[PathLikeInput] = None,
) -> JobPaths:
    resolved_job_root = None

    raw_job_root = job_root or os.getenv("VIDEO_JOB_ROOT")
    if raw_job_root:
        resolved_job_root = _resolve_existing_dir(raw_job_root, "job root")

    resolved_dataset_root = _resolve_optional_dir(dataset_root or os.getenv("VIDEO_DATASET_ROOT"))
    resolved_jobs_root = _resolve_optional_dir(jobs_root or os.getenv("VIDEO_JOBS_ROOT"))

    if resolved_jobs_root is None and resolved_dataset_root is not None:
        candidate_jobs_root = resolved_dataset_root / DEFAULT_JOBS_DIRNAME
        if candidate_jobs_root.is_dir():
            resolved_jobs_root = candidate_jobs_root.resolve()

    if resolved_job_root is None:
        resolved_job_id = job_id or os.getenv("VIDEO_JOB_ID")
        if not resolved_job_id:
            raise ValueError(
                "Missing job selection. Provide --job-root, --job-id, VIDEO_JOB_ROOT, or VIDEO_JOB_ID."
            )

        if resolved_jobs_root is None:
            fallback_dataset_root = _resolve_existing_dir(DEFAULT_DATASET_ROOT, "default dataset root")
            resolved_dataset_root = fallback_dataset_root
            resolved_jobs_root = _resolve_existing_dir(
                fallback_dataset_root / DEFAULT_JOBS_DIRNAME,
                "default jobs root",
            )

        candidate_job_root = resolved_jobs_root / resolved_job_id
        if not candidate_job_root.is_dir():
            raise FileNotFoundError(f"Could not find job root: {candidate_job_root}")
        resolved_job_root = candidate_job_root.resolve()

    if resolved_jobs_root is None:
        resolved_jobs_root = resolved_job_root.parent.resolve()

    if resolved_dataset_root is None:
        if resolved_jobs_root.name == DEFAULT_JOBS_DIRNAME:
            resolved_dataset_root = resolved_jobs_root.parent.resolve()
        else:
            fallback_dataset_root = _resolve_optional_dir(DEFAULT_DATASET_ROOT)
            resolved_dataset_root = fallback_dataset_root or resolved_jobs_root.resolve()

    return JobPaths(
        dataset_root=resolved_dataset_root,
        jobs_root=resolved_jobs_root,
        job_root=resolved_job_root,
    )


def coerce_job_paths(job_root: Union[JobPaths, PathLikeInput]) -> JobPaths:
    if isinstance(job_root, JobPaths):
        return job_root
    return resolve_job_paths(job_root=job_root)
