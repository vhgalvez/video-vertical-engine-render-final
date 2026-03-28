import argparse
from src.director_editor import build_timeline
from src.job_paths import resolve_job_paths
from src.renderer import render

def main(job_root=None, job_id=None):
    job_paths = resolve_job_paths(job_root=job_root, job_id=job_id)

    print(f"📁 Dataset root: {job_paths.dataset_root}")
    print(f"🗂️ Jobs root: {job_paths.jobs_root}")
    print(f"🎯 Job root: {job_paths.job_root}")

    print("🧠 Generando timeline...")
    build_timeline(job_paths)

    print("🎬 Renderizando video...")
    output = render(job_paths)

    print(f"✅ Video final: {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-root")
    parser.add_argument("--job-id")
    args = parser.parse_args()

    main(job_root=args.job_root, job_id=args.job_id)
