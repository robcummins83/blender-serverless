# Blender Serverless

RunPod serverless endpoint for GPU-accelerated Blender B-roll generation.

## Quick Start

### 1. Fork/Clone & Push
```bash
git clone https://github.com/YOUR_USERNAME/blender-serverless.git
cd blender-serverless
git push origin main
```

GitHub Actions will automatically build and push the Docker image to `ghcr.io/YOUR_USERNAME/blender-serverless:latest`

### 2. Create RunPod Endpoint

1. Go to [runpod.io/console/serverless](https://www.runpod.io/console/serverless)
2. Click **New Endpoint**
3. Configure:
   - **Name**: blender-broll
   - **Container Image**: `ghcr.io/YOUR_USERNAME/blender-serverless:latest`
   - **GPU**: RTX 4090 or RTX 3090
   - **Container Disk**: 20 GB
4. Copy your **Endpoint ID**

### 3. Use the API

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "template": "neural_network",
      "duration": 8,
      "resolution": [1920, 1080],
      "samples": 128
    }
  }'
```

Response contains base64-encoded MP4 video.

## Available Templates

| Template | Description |
|----------|-------------|
| `neural_network` | 3D neural network with glowing nodes and connections |
| `data_flow` | Particles flowing along paths to central node |

## API Reference

### Request

```json
{
  "input": {
    "template": "neural_network",
    "duration": 8,
    "resolution": [1920, 1080],
    "samples": 128,
    "fps": 30
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `template` | string | `neural_network` | Template name |
| `duration` | int | `8` | Video duration in seconds |
| `resolution` | [int, int] | `[1920, 1080]` | Width x Height |
| `samples` | int | `128` | Render quality (higher = better) |
| `fps` | int | `30` | Frames per second |

### Response

```json
{
  "video_base64": "AAAAIGZ0eXBpc29t...",
  "template": "neural_network",
  "duration": 8,
  "resolution": [1920, 1080],
  "render_time_seconds": 185.5,
  "file_size_bytes": 2456789,
  "gpu_used": true
}
```

## Pricing Estimate

| GPU | Cost/sec | 8s clip (~3 min render) |
|-----|----------|------------------------|
| RTX 4090 | $0.00069 | ~$0.12 |
| RTX 3090 | $0.00044 | ~$0.08 |

## Local Development

Test locally with Blender installed:

```bash
blender --background --python templates/neural_network_broll.py -- --output test.mp4
```

## License

MIT
