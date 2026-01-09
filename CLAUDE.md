# Blender Serverless - RunPod GPU Rendering

## Overview

Serverless Blender rendering on RunPod for generating B-roll clips. Uses BlenderKit .blend templates rendered with GPU acceleration.

---

## IMPORTANT: Render Workflow (DO NOT REBUILD DOCKER)

**The Docker image does NOT need to be rebuilt for template changes.**

RunPod fetches templates from GitHub at runtime using `template_url`. The workflow is:

### To render with template changes:

1. **Make changes to template** (e.g., modify .blend file or adjustment scripts)
2. **Commit and push to GitHub** (any branch - does NOT trigger rebuild unless pushing to main)
3. **Update `render.py` CONFIG** with the raw GitHub URL:
   ```python
   CONFIG = {
       "template_url": "https://raw.githubusercontent.com/username/blender-serverless/branch/templates/template.blend",
       ...
   }
   ```
4. **Run `python render.py`** - RunPod downloads template from URL and renders

### What triggers a Docker rebuild (AVOID unless necessary):
- Pushing to `main` branch triggers GitHub Actions workflow
- Only rebuild when changing: handler.py, render_blend.py, Dockerfile, or system dependencies

### Single Source of Truth:
- All render parameters are in `render.py` CONFIG dict
- `handler.py` has NO defaults - everything must come from the caller
- Change settings by editing CONFIG, not handler.py

---

## Architecture

```
RunPod Serverless Endpoint (9ypr4dw7bjj7xi)
    │
    ▼
handler.py (receives job, returns base64 video)
    │
    ▼
render_blend.py (configures GPU, renders to PNG frames)
    │
    ▼
Blender 4.2 LTS (Cycles GPU rendering with OptiX/CUDA)
    │
    ▼
FFmpeg NVENC (GPU-accelerated H264 encoding)
```

## Project Structure

```
blender-serverless/
├── render.py           # Client script - SINGLE SOURCE OF TRUTH for all render params
├── handler.py          # RunPod serverless handler (NO defaults - receives params from caller)
├── render_blend.py     # Generic .blend file renderer
├── Dockerfile          # Container with Blender 4.2 + CUDA
├── templates/          # Branded .blend templates (ready for render)
│   └── ai_cpu_activation_branded.blend
├── scripts/            # One script per template for branding modifications
│   └── ai_cpu_activation.py        # Branding for ai_cpu_activation.blend
└── CLAUDE.md
```

## Templates

All templates are BlenderKit .blend files stored in `templates/`:

| Template | File | Description |
|----------|------|-------------|
| `ai_cpu_activation` | `ai_cpu_activation.blend` | AI CPU activation animation |

To add new templates:
1. Download from BlenderKit
2. Save to `templates/your_template.blend`
3. Add to `TEMPLATES` dict in `handler.py`

## Render Pipeline

### Two-Stage Process

1. **Blender Cycles** renders frames to PNG (GPU-accelerated)
2. **FFmpeg NVENC** encodes PNGs to H264 MP4 (GPU-accelerated)

### GPU Acceleration

**Blender Cycles:**
- Tries **OptiX first** (2-3x faster on RTX, uses RT cores)
- Falls back to CUDA if OptiX unavailable
- Device priority: OptiX > CUDA > HIP > ONEAPI > METAL

**FFmpeg NVENC:**
- Uses `-hwaccel cuda` for input decoding
- Uses `h264_nvenc` for H264 encoding
- Requires `NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics,video` in Docker

### Error Handling

- NVENC encoding failure raises RuntimeError (no CPU fallback)
- Missing GPU raises RuntimeError
- This ensures issues are caught immediately rather than silently degrading

## Configuration

### render.py (SINGLE SOURCE OF TRUTH)
```python
CONFIG = {
    # Template settings
    "template": "ai_cpu_activation",
    "template_url": None,  # Set to GitHub raw URL to download at runtime

    # Render settings
    "duration": None,       # None = use full template animation, or set seconds
    "resolution": [1920, 1080],
    "samples": 128,
    "fps": 24,              # Match template fps (ai_cpu_activation is 24fps)

    # Polling settings
    "poll_interval": 10,    # Seconds between status checks
    "timeout": 2100,        # 35 minutes max wait
}
```

### handler.py (NO DEFAULTS)
```python
# handler.py has NO default values - all params must come from render.py
# This ensures single source of truth and no hidden behavior
DEFAULT_CONFIG = {
    "duration": None,
    "resolution": None,  # Required
    "samples": None,     # Required
    "fps": None,         # Required
}
```

### render_blend.py
- Render engine: Cycles
- Device priority: OptiX > CUDA > HIP > ONEAPI > METAL
- Denoising: Enabled
- Output: PNG frames → NVENC H264 MP4

## API

### Request (using template name)
```json
{
    "input": {
        "template": "ai_cpu_activation",
        "resolution": [1920, 1080],
        "samples": 128,
        "fps": 24
    }
}
```

### Request (using template URL - preferred for template changes)
```json
{
    "input": {
        "template_url": "https://raw.githubusercontent.com/.../template.blend",
        "resolution": [1920, 1080],
        "samples": 128,
        "fps": 24,
        "duration": 8
    }
}
```

### Response
```json
{
    "video_base64": "...",
    "template": "ai_cpu_activation",
    "duration": 8,
    "resolution": [1920, 1080],
    "render_time_seconds": 180,
    "file_size_bytes": 1234567,
    "gpu_used": true
}
```

## Environment Variables

```bash
RUNPOD_API_KEY=your_key
RUNPOD_ENDPOINT_ID=9ypr4dw7bjj7xi
```

## Running a Render

```bash
# Edit CONFIG in render.py first, then:
python render.py
```

Output saved to `output.mp4` in current directory.

## Docker Configuration

### Base Image
`nvidia/cuda:12.1.0-devel-ubuntu22.04`

### Required Capabilities
```dockerfile
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics,video
```

The `video` capability is required for NVENC encoding.

### Installed Components
- Blender 4.2 LTS (bundled CUDA/OptiX runtime)
- FFmpeg (with NVENC support)
- Python 3 + runpod SDK
- xvfb (headless display for GPU initialization)

## Dependencies

- Blender 4.2 LTS
- FFmpeg with NVENC
- Python 3
- xvfb
- runpod SDK
