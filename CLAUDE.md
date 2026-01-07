# Blender Serverless - RunPod GPU Rendering

## Overview

Serverless Blender rendering on RunPod for generating B-roll clips. Supports both procedural Python templates and pre-made .blend files.

## Architecture

```
RunPod Serverless Endpoint
    │
    ▼
handler.py (receives job, returns base64 video)
    │
    ▼
render_blend.py (configures GPU, renders animation)
    │
    ▼
Blender 4.2 LTS (Cycles GPU rendering)
```

## Templates

### Procedural (Python scripts)
- `templates/neural_network_broll.py` - Neural network visualization
- `templates/data_flow_broll.py` - Data flow animation

### Blend Files (pre-made)
- `blend_templates/ai_cpu_activation.blend` - AI CPU activation animation

## Render Engine

Uses **Cycles** with GPU acceleration:
- Tries **OptiX first** (2-3x faster on RTX, uses RT cores)
- Falls back to CUDA if OptiX unavailable
- `render_blend.py:74` - Device priority order

## Current Issues

### Build Quota Exceeded (BLOCKING)

RunPod build fails with `disk quota exceeded` during cache export. The image builds successfully but cache write fails, causing RunPod to reject the deployment.

**Attempted fixes:**
1. Switch from `nvidia/cuda:12.1.0-devel` to `runtime` - Still failed
2. Switch to plain `ubuntu:22.04` - Still failed

**Root cause:** Account-level storage quota full from accumulated builds across all endpoints.

**Solutions:**
1. Contact RunPod support to clear build cache
2. Use a pre-built image from Docker Hub instead of building on RunPod
3. Delete all endpoints and try fresh account

### Render Performance (Untested due to build issue)

Previous tests showed:
- 8s clip at 64 samples took 17+ minutes before cancellation
- GPU telemetry showed intermittent usage (on/off pattern)
- Suspected cause: CUDA used instead of OptiX

**Fix applied but untested:**
- Changed device priority to try OptiX first (`render_blend.py:74`)

## Configuration

### handler.py
```python
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
- Output: H264 MP4

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

## Testing

```bash
# Local test
python test_endpoint.py

# Set environment variables
RUNPOD_API_KEY=your_key
RUNPOD_ENDPOINT_ID=your_endpoint_id
```

## Dependencies

- Blender 4.2 LTS (bundled CUDA/OptiX)
- Python 3
- FFmpeg
- xvfb (headless display)
- runpod SDK

## Docker Base Image History

| Image | Size | Status |
|-------|------|--------|
| `nvidia/cuda:12.1.0-devel-ubuntu22.04` | ~5GB | Quota exceeded |
| `nvidia/cuda:12.1.0-runtime-ubuntu22.04` | ~2GB | Quota exceeded |
| `ubuntu:22.04` | ~70MB | Quota exceeded (cache) |

Blender 4.2 bundles its own CUDA/OptiX runtime, so nvidia base images aren't strictly required. The nvidia-docker runtime on RunPod provides the driver.
