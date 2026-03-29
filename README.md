# Video Vertical Final Render Engine

Motor de render final vertical automático que ejecuta fielmente el plan editorial ya definido aguas arriba en `source/<job_id>_visual_manifest.json`.

Este repositorio no usa LLMs ni toma decisiones semánticas. El upstream ya piensa. Aquí solo se ejecuta:

`visual_manifest.scene_plan -> matching manual por scene_id -> timeline_final.json -> video_base.mp4 -> video_with_audio.mp4 -> video_final.mp4`

## Qué haces tú manualmente

Solo dos cosas por job:

1. Poner imágenes en `jobs/<job_id>/images/`
2. Poner videos en `jobs/<job_id>/videos/`

Todo lo demás lo hace el repo:

- lee audio
- lee subtítulos
- lee `visual_manifest`
- usa `scene_plan` como fuente de verdad
- empata assets por `scene_id`
- construye `timeline_final.json`
- renderiza `video_base.mp4`
- añade narración
- quema subtítulos
- exporta `video_final.mp4`
- actualiza `status.json`

## Dataset real esperado

Raíz del dataset:

```text
/mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset
```

Jobs:

```text
/mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset/jobs
```

Estructura por job:

```text
jobs/<job_id>/
├── audio/
│   └── <job_id>_narration.wav
├── subtitles/
│   └── <job_id>_narration.srt
├── source/
│   ├── <job_id>_brief.json
│   ├── <job_id>_script.json
│   └── <job_id>_visual_manifest.json
├── images/
│   ├── scene_01.png
│   ├── scene_03.jpg
│   └── ...
├── videos/
│   ├── scene_02.mp4
│   ├── scene_04.mov
│   └── ...
├── timeline/
│   └── vertical/
│       └── timeline_final.json
├── output/
│   └── vertical/
│       ├── video_base.mp4
│       ├── video_with_audio.mp4
│       └── video_final.mp4
├── logs/
│   └── render_vertical.log
├── job.json
└── status.json
```

## Regla editorial fundamental

Cuando existe `visual_manifest.scene_plan`, el renderer:

- usa exactamente el orden del `scene_plan`
- usa exactamente `start_sec` y `end_sec`
- calcula `duration = end_sec - start_sec`
- hace matching estricto por `scene_id`
- preserva metadata editorial útil dentro del timeline

No monta escenas por orden arbitrario de archivos.

## Naming correcto de assets

Cada escena del `scene_plan` debe existir en `images/` o `videos/` con el mismo `scene_id`.

Para `scene_01`, el motor busca en este orden lógico:

- `videos/scene_01.mp4`
- `videos/scene_01.mov`
- `videos/scene_01.mkv`
- `videos/scene_01.webm`
- `images/scene_01.png`
- `images/scene_01.jpg`
- `images/scene_01.jpeg`
- `images/scene_01.webp`

Prioridad:

1. Si existe video, usa video.
2. Si no existe video pero sí imagen, usa imagen.
3. Si no existe ninguno, falla con error claro indicando el `scene_id` faltante.

Debe haber un solo asset por `scene_id` y tipo. Dos ficheros como `scene_01.mp4` y `scene_01.mov` para la misma escena producirán error.

## Fuente de verdad del timeline

El archivo clave es:

```text
source/<job_id>_visual_manifest.json
```

Se usa especialmente:

- `scene_plan`
- `scene_id`
- `scene_role`
- `start_sec`
- `end_sec`
- `text`
- `visual_intent`
- `camera`
- `mood`
- `transition`

El `timeline_final.json` generado preserva:

- `id`
- `scene_role`
- `type`
- `path`
- `start`
- `end`
- `duration`
- `text`
- `transition`
- `mood`
- `camera`
- `visual_intent`

Ejemplo:

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
      "duration": 7.01,
      "text": "Estás en un bucle.",
      "transition": "cold_open",
      "mood": "urgencia and immediate urgency",
      "camera": "extreme close-up or punch-in opening frame, direct subject emphasis",
      "visual_intent": "Open with an arresting visual contradiction that stops the scroll and frames the core thesis immediately."
    }
  ]
}
```

## Flujo real del pipeline

1. Lee `job.json`, `status.json`, audio, subtítulos y `visual_manifest`.
2. Carga `scene_plan`.
3. Valida que el plan sea contiguo.
4. Si el audio no coincide exactamente, conserva el `scene_plan` como fuente de verdad y paddea silencio si el audio queda corto.
5. Busca el asset correcto por `scene_id`.
6. Genera `timeline/vertical/timeline_final.json`.
7. Renderiza `output/vertical/video_base.mp4`.
8. Añade narración en `output/vertical/video_with_audio.mp4`.
9. Quema subtítulos en `output/vertical/video_final.mp4`.
10. Actualiza `status.json`.
11. Escribe logs claros en consola y en `logs/render_vertical.log`.

## Requisitos

- Python 3.11 o superior
- `ffmpeg` y `ffprobe` accesibles en `PATH`
- Dataset externo disponible

Instalación:

```bash
pip install -r requirements.txt
```

## CLI

Un solo job:

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

Todos los jobs:

```bash
python scripts/run_job.py \
  --jobs-root /mnt/c/Users/vhgal/Documents/desarrollo/ia/AI-video-automation/video-dataset/jobs \
  --all \
  --format vertical
```

## Salidas generadas

Por cada job:

- `timeline/vertical/timeline_final.json`
- `output/vertical/video_base.mp4`
- `output/vertical/video_with_audio.mp4`
- `output/vertical/video_final.mp4`

`status.json` se actualiza con campos como:

- `timeline_generated`
- `timeline_path`
- `render_started`
- `render_started_at`
- `render_finished`
- `render_finished_at`
- `final_video_path`
- `render_vertical_ready`
- `render_error`

## Logs esperados

El proceso deja trazabilidad como:

- job procesado
- `visual_manifest` cargado
- `scene_plan` cargado
- assets encontrados por `scene_id`
- escenas faltantes
- timeline generado
- archivo final generado

## Errores típicos

`Missing visual assets for scene_plan scenes`
Falta al menos un `scene_id` del `scene_plan` en `images/` o `videos/`.

`Duplicate image asset` o `Duplicate video asset`
Hay más de un fichero del mismo tipo para el mismo `scene_id`.

`scene_plan is not contiguous`
Los `start_sec` y `end_sec` no encadenan correctamente escena a escena.

`Desajuste entre scene_plan y audio`
No detiene el render por sí solo. El motor conserva el `scene_plan` y paddea silencio si el audio termina antes.

`Missing narration audio` o `Missing subtitle file`
Faltan artefactos upstream del job.

## Ejecución recomendada

1. Abre el `visual_manifest` del job y mira los `scene_id` del `scene_plan`.
2. Coloca tus assets manuales con esos mismos nombres en `images/` y `videos/`.
3. Ejecuta la CLI.
4. Revisa `output/vertical/video_final.mp4`.
5. Si falla, abre `logs/render_vertical.log`.
