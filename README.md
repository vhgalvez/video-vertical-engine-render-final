# Video Vertical Final Render Engine

Motor de render final automático para videos verticales a partir de un dataset externo real de jobs. El flujo toma un job ya preparado con narración, subtítulos y `visual_manifest`, detecta assets manuales en `images/` y `videos/`, construye `timeline_final.json` priorizando `scene_plan`, renderiza la base visual, añade audio y quema subtítulos.

## Dataset esperado

Raíz del dataset:

```text
/mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset
```

Jobs:

```text
/mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset/jobs
```

Estructura real por job:

```text
jobs/<job_id>/
  audio/
    <job_id>_narration.wav
  subtitles/
    <job_id>_narration.srt
  source/
    <job_id>_brief.json
    <job_id>_script.json
    <job_id>_visual_manifest.json
  images/
    scene_01.png
    scene_03.jpg
    ...
  videos/
    scene_02.mp4
    scene_05.mov
    ...
  timeline/
    vertical/
      timeline_final.json
  output/
    vertical/
      video_base.mp4
      video_with_audio.mp4
      video_final.mp4
  logs/
  job.json
  status.json
```

## Regla de naming de assets

El motor usa el `scene_plan` de `source/<job_id>_visual_manifest.json` como fuente prioritaria. Cada escena debe resolverse por su `scene_id` real.

Ejemplos válidos:

- `scene_01.png`
- `scene_01.jpg`
- `scene_01.jpeg`
- `scene_01.webp`
- `scene_01.mp4`
- `scene_01.mov`
- `scene_01.mkv`
- `scene_01.webm`

Prioridad de matching:

1. Si existe video para `scene_id`, se usa el video.
2. Si no existe video pero sí imagen, se usa la imagen.
3. Si no existe ninguno, el proceso falla con error claro indicando el `scene_id` faltante.

No se usa naming por defecto tipo `scene_001` ni fallback posicional cuando existe `scene_plan`.

## Qué hace el pipeline

1. Lee `job.json`, `status.json` y `source/<job_id>_visual_manifest.json`.
2. Detecta assets manuales en `images/` y `videos/`.
3. Construye `timeline/vertical/timeline_final.json`.
4. Renderiza `output/vertical/video_base.mp4`.
5. Añade narración y genera `output/vertical/video_with_audio.mp4`.
6. Quema subtítulos y genera `output/vertical/video_final.mp4`.
7. Actualiza `status.json` con:
   `timeline_generated`, `render_started`, `render_finished`, `final_video_path`, `render_vertical_ready`.

## Timeline generado

El timeline final tiene este formato:

```json
{
  "format": "vertical",
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "audio_path": "audio/000001_narration.wav",
  "subtitle_path": "subtitles/000001_narration.srt",
  "total_duration": 60.0,
  "scenes": [
    {
      "id": "scene_01",
      "scene_role": "hook",
      "type": "image",
      "path": "images/scene_01.png",
      "start": 0.0,
      "end": 7.01,
      "duration": 7.01
    }
  ]
}
```

Si `scene_plan` no existe, el motor hace fallback: detecta assets disponibles y reparte el audio total en segmentos equitativos.

## Requisitos

- Python 3.11 o superior
- `ffmpeg` y `ffprobe` instalados y accesibles en `PATH`
- Dataset externo disponible en Windows o WSL

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecutar un job

```bash
python scripts/run_job.py \
  --jobs-root /mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset/jobs \
  --job-id 000001 \
  --format vertical
```

En PowerShell:

```powershell
python scripts/run_job.py `
  --jobs-root C:\Users\vhgal\Documents\desarrollo\ia\AI-video-automation\video-dataset\jobs `
  --job-id 000001 `
  --format vertical
```

## Ejecutar todos los jobs

```bash
python scripts/run_job.py \
  --jobs-root /mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset/jobs \
  --all \
  --format vertical
```

## Logging esperado

El comando imprime:

- job procesado
- `visual_manifest` cargado
- `scene_plan` detectado
- assets encontrados por `scene_id`
- timeline generado
- duración del audio
- ruta final del mp4

## Salidas generadas

Por cada job:

- `timeline/vertical/timeline_final.json`
- `output/vertical/video_base.mp4`
- `output/vertical/video_with_audio.mp4`
- `output/vertical/video_final.mp4`

## Flujo recomendado

1. Genera o recibe un job ya completo con audio, subtítulos y `visual_manifest`.
2. Copia manualmente tus assets visuales a `images/` y `videos/` usando el `scene_id` exacto del `scene_plan`.
3. Ejecuta `scripts/run_job.py`.
4. Revisa `output/vertical/video_final.mp4`.
