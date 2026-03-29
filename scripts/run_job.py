from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.job_paths import (
    DEFAULT_DATASET_ROOT,
    DEFAULT_JOBS_DIRNAME,
    ensure_supported_format,
    normalize_path,
    resolve_job_paths,
)
from src.renderer import render


LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


def iter_job_ids(jobs_root: Path) -> list[str]:
    return sorted(entry.name for entry in jobs_root.iterdir() if entry.is_dir())


def run_single_job(jobs_root: str | None, job_id: str, render_format: str) -> str:
    job_paths = resolve_job_paths(jobs_root=jobs_root, job_id=job_id)
    LOGGER.info("Procesando job %s en %s", job_id, job_paths.job_root)
    final_output = render(job_paths, render_format=render_format)
    LOGGER.info("Job %s completado. Video final: %s", job_id, final_output)
    return final_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render final automatizado para videos verticales.")
    parser.add_argument("--jobs-root", help="Ruta a la carpeta jobs del dataset externo.")
    parser.add_argument("--job-id", help="ID del job a renderizar.")
    parser.add_argument("--all", action="store_true", help="Procesa todos los jobs dentro de jobs-root.")
    parser.add_argument("--format", default="vertical", help="Formato de render. Actualmente solo soporta vertical.")
    return parser.parse_args()


def resolve_jobs_root_for_all(raw_jobs_root: str | None) -> Path:
    if raw_jobs_root:
        return normalize_path(raw_jobs_root)

    env_jobs_root = os.getenv("VIDEO_JOBS_ROOT")
    if env_jobs_root:
        return normalize_path(env_jobs_root)

    env_dataset_root = os.getenv("VIDEO_DATASET_ROOT")
    if env_dataset_root:
        return normalize_path(Path(env_dataset_root) / DEFAULT_JOBS_DIRNAME)

    return normalize_path(Path(DEFAULT_DATASET_ROOT) / DEFAULT_JOBS_DIRNAME)


def main() -> int:
    configure_logging()
    args = parse_args()
    render_format = ensure_supported_format(args.format)

    if args.all and args.job_id:
        raise ValueError("Use --job-id o --all, pero no ambos a la vez.")
    if not args.all and not args.job_id:
        raise ValueError("Debe indicar --job-id o --all.")

    jobs_root = str(normalize_path(args.jobs_root)) if args.jobs_root else None

    job_ids = (
        iter_job_ids(resolve_jobs_root_for_all(jobs_root))
        if args.all
        else [args.job_id]
    )
    failures: list[tuple[str, str]] = []

    for job_id in job_ids:
        try:
            run_single_job(jobs_root, job_id, render_format)
        except Exception as exc:
            failures.append((job_id, str(exc)))
            LOGGER.exception("Fallo procesando job %s", job_id)

    if failures:
        for job_id, message in failures:
            LOGGER.error("Job fallido %s: %s", job_id, message)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
