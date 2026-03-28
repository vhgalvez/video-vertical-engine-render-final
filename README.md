# Video Pipeline Engine

## Ejecutar

pip install -r requirements.txt

python scripts/run_job.py --job-root /ruta/al/job/000001

python scripts\run_job.py --job-root "C:\Users\vhgal\Documents\desarrollo\ia\neurocontent-engine\jobs\000001"

## Dataset externo compartido

El repositorio ya puede resolver rutas del dataset compartido de forma centralizada.

Orden de resolución:

1. `--job-root`
2. `VIDEO_JOB_ROOT`
3. `--job-id` o `VIDEO_JOB_ID` combinado con `VIDEO_JOBS_ROOT`
4. `--job-id` o `VIDEO_JOB_ID` combinado con `VIDEO_DATASET_ROOT/jobs`
5. fallback por defecto a `/mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset/jobs`

Variables soportadas:

- `VIDEO_DATASET_ROOT`
- `VIDEO_JOBS_ROOT`
- `VIDEO_JOB_ROOT`
- `VIDEO_JOB_ID`

Ejemplos:

python scripts/run_job.py --job-root /mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset/jobs/000001

python scripts/run_job.py --job-id 000001

PowerShell:

```powershell
$env:VIDEO_DATASET_ROOT="C:\Users\vhgal\Documents\desarrollo\ia\AI-video-automation\video-dataset"
python scripts\run_job.py --job-id 000001
```

Rutas del job centralizadas:

- `visual_manifest.json` o `source/visual_manifest.json`
- `audio/narration.wav`
- `subtitles/narration.srt`
- `images/`
- `videos/`
- `timeline/timeline_final.json`
- `output/video_base.mp4`
- `output/video_with_audio.mp4`
- `output/video_final.mp4`
