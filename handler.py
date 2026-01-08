"""
RunPod Serverless Handler for Blender B-Roll Generation

Accepts render requests via HTTP API and returns rendered video.

Request format:
{
    "input": {
        "template": "neural_network",  # or "data_flow", etc.
        "duration": 8,
        "resolution": [1920, 1080],
        "samples": 128,
        "config": {}  # Optional template-specific config
    }
}

Response format:
{
    "output": {
        "video_base64": "...",  # Base64 encoded MP4
        "duration": 8,
        "resolution": [1920, 1080],
        "render_time_seconds": 180
    }
}
"""

import runpod
import subprocess
import base64
import time
import os
import json
import tempfile
from pathlib import Path

# Blend file templates (BlenderKit templates)
TEMPLATES = {
    "ai_cpu_activation": "/workspace/templates/ai_cpu_activation.blend",
}

# Default config
DEFAULT_CONFIG = {
    "duration": 8,
    "resolution": [1920, 1080],
    "samples": 128,
    "fps": 30,
}


def check_gpu():
    """Check if GPU is available."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            gpu_name = result.stdout.strip()
            print(f"GPU detected: {gpu_name}")
            return True
    except Exception as e:
        print(f"GPU check failed: {e}")
    return False


def render_blender(template: str, output_path: str, config: dict) -> dict:
    """
    Execute Blender render for a .blend template file.

    Returns dict with success status and timing info.
    """
    if template not in TEMPLATES:
        return {
            "success": False,
            "error": f"Unknown template: {template}. Available: {list(TEMPLATES.keys())}"
        }

    template_path = TEMPLATES[template]

    if not os.path.exists(template_path):
        return {
            "success": False,
            "error": f"Template not found: {template_path}"
        }

    # Build Blender command with xvfb-run for GPU initialization
    cmd = [
        "xvfb-run",
        "-a",
        "--server-args=-screen 0 1920x1080x24",
        "blender",
        "--background",
        template_path,  # Load the .blend file
        "--python", "/workspace/render_blend.py",
        "--",
        "--output", output_path,
        "--width", str(config.get("resolution", [1920, 1080])[0]),
        "--height", str(config.get("resolution", [1920, 1080])[1]),
        "--samples", str(config.get("samples", 128)),
        "--fps", str(config.get("fps", 30)),
    ]
    # Only add duration if explicitly set (otherwise use file's animation)
    if config.get("duration"):
        cmd.extend(["--duration", str(config["duration"])])

    print(f"Executing: {' '.join(cmd)}")
    start_time = time.time()

    try:
        # Run with output streaming so we can see Blender's GPU detection
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )

        render_time = time.time() - start_time

        # Print Blender output for debugging
        if result.stdout:
            print("=== BLENDER STDOUT ===")
            for line in result.stdout.split('\n')[-50:]:  # Last 50 lines
                print(line)
        if result.stderr:
            print("=== BLENDER STDERR ===")
            for line in result.stderr.split('\n')[-20:]:  # Last 20 lines
                print(line)

        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            return {
                "success": True,
                "render_time_seconds": round(render_time, 2),
                "file_size_bytes": file_size,
                "stdout": result.stdout[-2000:] if result.stdout else None,
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Render failed - no output file",
                "stdout": result.stdout[-2000:] if result.stdout else None,
                "render_time_seconds": round(render_time, 2),
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Render timed out after 1 hour"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handler(job):
    """
    RunPod serverless handler function.

    Called for each incoming request.
    """
    print(f"Received job: {job['id']}")

    job_input = job.get("input", {})

    # Extract parameters
    template = job_input.get("template", "neural_network")
    config = {**DEFAULT_CONFIG}

    if "duration" in job_input:
        config["duration"] = job_input["duration"]
    if "resolution" in job_input:
        config["resolution"] = job_input["resolution"]
    if "samples" in job_input:
        config["samples"] = job_input["samples"]
    if "fps" in job_input:
        config["fps"] = job_input["fps"]
    if "config" in job_input:
        config.update(job_input["config"])

    print(f"Template: {template}")
    print(f"Config: {config}")

    # Check GPU
    has_gpu = check_gpu()
    if not has_gpu:
        print("WARNING: No GPU detected, render will be slow")

    # Create temp output file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        output_path = tmp.name

    try:
        # Render
        print(f"Starting render to: {output_path}")
        render_result = render_blender(template, output_path, config)

        if not render_result["success"]:
            return {"error": render_result.get("error", "Render failed")}

        # Read and encode output
        with open(output_path, "rb") as f:
            video_bytes = f.read()

        video_base64 = base64.b64encode(video_bytes).decode("utf-8")

        return {
            "video_base64": video_base64,
            "template": template,
            "duration": config["duration"],
            "resolution": config["resolution"],
            "render_time_seconds": render_result["render_time_seconds"],
            "file_size_bytes": render_result["file_size_bytes"],
            "gpu_used": has_gpu,
        }

    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)


# For local testing
def test_local():
    """Test handler locally."""
    test_job = {
        "id": "test-123",
        "input": {
            "template": "neural_network",
            "duration": 4,
            "samples": 32,
        }
    }

    result = handler(test_job)

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Success!")
        print(f"  Render time: {result['render_time_seconds']}s")
        print(f"  File size: {result['file_size_bytes']} bytes")

        video_bytes = base64.b64decode(result["video_base64"])
        with open("test_output.mp4", "wb") as f:
            f.write(video_bytes)
        print(f"  Saved to: test_output.mp4")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_local()
    else:
        print("Starting RunPod Blender serverless worker...")
        runpod.serverless.start({"handler": handler})
