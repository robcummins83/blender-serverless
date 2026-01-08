# Blender Serverless - RunPod GPU Rendering

## Overview

Serverless Blender rendering on RunPod for generating B-roll clips. Uses BlenderKit .blend templates rendered with GPU acceleration.

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
├── handler.py          # RunPod serverless handler
├── render_blend.py     # Generic .blend file renderer
├── Dockerfile          # Container with Blender 4.2 + CUDA
├── templates/          # BlenderKit .blend templates
│   └── ai_cpu_activation.blend
├── test_endpoint.py    # Endpoint testing script
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

### handler.py
```python
TEMPLATES = {
    "ai_cpu_activation": "/workspace/templates/ai_cpu_activation.blend",
}

DEFAULT_CONFIG = {
    "duration": 8,
    "resolution": [1920, 1080],
    "samples": 128,
    "fps": 30,
}
```

### render_blend.py
- Render engine: Cycles
- Device priority: OptiX > CUDA > HIP > ONEAPI > METAL
- Denoising: Enabled
- Output: PNG frames → NVENC H264 MP4

## API

### Request
```json
{
    "input": {
        "template": "ai_cpu_activation",
        "duration": 8,
        "resolution": [1920, 1080],
        "samples": 64
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

## Testing

```bash
python test_endpoint.py
```

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
