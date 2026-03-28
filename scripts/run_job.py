import argparse
from src.director_editor import build_timeline
from src.renderer import render

def main(job_root):
    print("🧠 Generando timeline...")
    build_timeline(job_root)

    print("🎬 Renderizando video...")
    output = render(job_root)

    print(f"✅ Video final: {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-root", required=True)
    args = parser.parse_args()

    main(args.job_root)
