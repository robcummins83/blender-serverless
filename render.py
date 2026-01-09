"""
RunPod Blender render client

SINGLE SOURCE OF TRUTH: All render parameters are defined in CONFIG below.
The handler.py has no defaults - all values come from here.
"""

import os
import requests
import base64
import time
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# SINGLE SOURCE OF TRUTH - All render parameters defined here
# =============================================================================
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
# =============================================================================

# API credentials from environment
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")
ENDPOINT_ID = os.environ.get("RUNPOD_BLENDER_ENDPOINT_ID") or "9ypr4dw7bjj7xi"

if not RUNPOD_API_KEY:
    print("ERROR: Set RUNPOD_API_KEY in environment or .env")
    exit(1)

BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json",
}


def run_render():
    """Submit render job to RunPod and poll for completion."""
    print("=" * 50)
    print(f"Blender 4.2 + CUDA Render")
    print(f"Template: {CONFIG['template'] or 'from URL'}")
    print(f"Duration: {CONFIG['duration'] or 'full animation'}")
    print(f"Resolution: {CONFIG['resolution']}")
    print(f"Samples: {CONFIG['samples']}")
    print(f"FPS: {CONFIG['fps']}")
    print("=" * 50)

    # Build payload from CONFIG - all parameters explicit
    payload = {
        "input": {
            "resolution": CONFIG["resolution"],
            "samples": CONFIG["samples"],
            "fps": CONFIG["fps"],
        }
    }

    # Template: either by name or URL
    if CONFIG["template_url"]:
        payload["input"]["template_url"] = CONFIG["template_url"]
    else:
        payload["input"]["template"] = CONFIG["template"]

    # Duration: only add if specified (None = use full template animation)
    if CONFIG["duration"]:
        payload["input"]["duration"] = CONFIG["duration"]

    # Submit job (async)
    print("Submitting job...")
    response = requests.post(
        f"{BASE_URL}/run",
        headers=HEADERS,
        json=payload,
    )

    if response.status_code != 200:
        print(f"ERROR: HTTP {response.status_code}")
        print(response.text)
        return

    data = response.json()
    job_id = data.get("id")
    print(f"Job ID: {job_id}")

    # Poll for completion
    start_time = time.time()
    while True:
        elapsed = int(time.time() - start_time)

        status_response = requests.get(
            f"{BASE_URL}/status/{job_id}",
            headers=HEADERS,
        )

        status_data = status_response.json()
        status = status_data.get("status")

        print(f"[{elapsed}s] Status: {status}")

        if status == "COMPLETED":
            output = status_data.get("output", {})

            print("\n" + "=" * 50)
            print("SUCCESS!")
            print("=" * 50)
            print(f"Template: {output.get('template')}")
            print(f"Duration: {output.get('duration')}s")
            print(f"Resolution: {output.get('resolution')}")
            print(f"Render time: {output.get('render_time_seconds')}s")
            print(f"File size: {output.get('file_size_bytes'):,} bytes")
            print(f"GPU used: {output.get('gpu_used')}")

            # Save video
            video_base64 = output.get("video_base64")
            if video_base64:
                video_bytes = base64.b64decode(video_base64)
                output_path = "output.mp4"
                with open(output_path, "wb") as f:
                    f.write(video_bytes)
                print(f"\nSaved to: {output_path}")
            break

        elif status == "FAILED":
            print("\n" + "=" * 50)
            print("FAILED")
            print("=" * 50)
            print(f"Error: {status_data.get('error')}")
            # Show full response for debugging
            output = status_data.get("output", {})
            if output:
                print(f"\nOutput details:")
                for k, v in output.items():
                    if k != "video_base64":  # Skip the big base64 blob
                        print(f"  {k}: {v}")
            break

        elif elapsed > CONFIG["timeout"]:
            print(f"Timeout: Job exceeded {CONFIG['timeout']}s limit")
            break

        time.sleep(CONFIG["poll_interval"])


if __name__ == "__main__":
    # All render parameters come from CONFIG at top of file
    # Edit CONFIG directly to change settings - single source of truth
    run_render()
