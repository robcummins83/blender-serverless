"""
RunPod Serverless Handler for Blender B-Roll Generation

Accepts render requests via HTTP API and returns rendered video.

Request format:
{
    "input": {
        "template": "ai_cpu_activation",  # Use baked-in template by name
        # OR
        "template_url": "https://raw.githubusercontent.com/.../template.blend",  # Download at runtime

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
import urllib.request
import urllib.error
from pathlib import Path

# Blend file templates (branded versions)
TEMPLATES = {
    "ai_cpu_activation": "/workspace/templates/ai_cpu_activation_branded.blend",
}

# No defaults - all parameters must be passed from calling script
# This ensures single source of truth and no hidden behavior
DEFAULT_CONFIG = {
    "duration": None,      # None = use full template animation
    "resolution": None,    # Required from caller
    "samples": None,       # Required from caller
    "fps": None,           # Required from caller
}


def download_template(url: str) -> str:
    """
    Download a .blend template from URL to a temp file.

    Returns path to downloaded file.
    Raises exception on failure.
    """
    print(f"Downloading template from: {url}")

    # Create temp file with .blend extension
    fd, temp_path = tempfile.mkstemp(suffix=".blend")
    os.close(fd)

    try:
        # Download with timeout
        req = urllib.request.Request(url, headers={"User-Agent": "RunPod-Blender/1.0"})
        with urllib.request.urlopen(req, timeout=120) as response:
            content = response.read()

        # Write to temp file
        with open(temp_path, "wb") as f:
            f.write(content)

        file_size = os.path.getsize(temp_path)
        print(f"Downloaded template: {file_size} bytes -> {temp_path}")
        return temp_path

    except urllib.error.HTTPError as e:
        os.remove(temp_path)
        raise Exception(f"HTTP error downloading template: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        os.remove(temp_path)
        raise Exception(f"URL error downloading template: {e.reason}")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise Exception(f"Failed to download template: {e}")


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


def render_blender(template_path: str, output_path: str, config: dict) -> dict:
    """
    Execute Blender render for a .blend template file.

    Args:
        template_path: Full path to .blend file
        output_path: Where to save rendered MP4
        config: Render configuration dict

    Returns dict with success status and timing info.
    """
    if not os.path.exists(template_path):
        return {
            "success": False,
            "error": f"Template not found: {template_path}"
        }

    # Validate required parameters
    resolution = config.get("resolution")
    samples = config.get("samples")
    fps = config.get("fps")

    if not resolution:
        return {"success": False, "error": "Missing required parameter: resolution"}
    if not samples:
        return {"success": False, "error": "Missing required parameter: samples"}
    if not fps:
        return {"success": False, "error": "Missing required parameter: fps"}

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
        "--width", str(resolution[0]),
        "--height", str(resolution[1]),
        "--samples", str(samples),
        "--fps", str(fps),
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
    template_name = job_input.get("template")
    template_url = job_input.get("template_url")
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

    # Resolve template path
    downloaded_template = None
    if template_url:
        # Download template from URL
        print(f"Template URL: {template_url}")
        try:
            template_path = download_template(template_url)
            downloaded_template = template_path  # Track for cleanup
        except Exception as e:
            return {"error": f"Failed to download template: {e}"}
    elif template_name:
        # Use baked-in template by name
        if template_name not in TEMPLATES:
            return {"error": f"Unknown template: {template_name}. Available: {list(TEMPLATES.keys())}"}
        template_path = TEMPLATES[template_name]
        print(f"Template: {template_name} -> {template_path}")
    else:
        # Default to first available template
        template_name = "ai_cpu_activation"
        template_path = TEMPLATES[template_name]
        print(f"Template: {template_name} (default) -> {template_path}")

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
        render_result = render_blender(template_path, output_path, config)

        if not render_result["success"]:
            return {"error": render_result.get("error", "Render failed")}

        # Read and encode output
        with open(output_path, "rb") as f:
            video_bytes = f.read()

        video_base64 = base64.b64encode(video_bytes).decode("utf-8")

        return {
            "video_base64": video_base64,
            "template": template_name or "from_url",
            "template_url": template_url,
            "duration": config["duration"],
            "resolution": config["resolution"],
            "render_time_seconds": render_result["render_time_seconds"],
            "file_size_bytes": render_result["file_size_bytes"],
            "gpu_used": has_gpu,
        }

    finally:
        # Cleanup output file
        if os.path.exists(output_path):
            os.remove(output_path)
        # Cleanup downloaded template
        if downloaded_template and os.path.exists(downloaded_template):
            os.remove(downloaded_template)
            print(f"Cleaned up downloaded template: {downloaded_template}")


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
