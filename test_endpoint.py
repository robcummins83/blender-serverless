"""
Test the RunPod Blender serverless endpoint (async with polling)
"""

import os
import requests
import base64
import time
from dotenv import load_dotenv

load_dotenv()

# Config - set these in .env or environment
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")
ENDPOINT_ID = os.environ.get("RUNPOD_BLENDER_ENDPOINT_ID")

if not RUNPOD_API_KEY:
    print("ERROR: Set RUNPOD_API_KEY in environment or .env")
    exit(1)

if not ENDPOINT_ID:
    print("ERROR: Set RUNPOD_BLENDER_ENDPOINT_ID in environment or .env")
    exit(1)

BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json",
}


def test_render():
    """Test a simple render using async /run endpoint with polling."""
    print("=" * 50)
    print("Testing Blender 4.2 + CUDA")
    print("=" * 50)

    payload = {
        "input": {
            "template": "neural_network",
            "duration": 4,          # Short for testing
            "resolution": [1920, 1080],
            "samples": 64,          # Lower for faster test
        }
    }

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
                output_path = "test_output.mp4"
                with open(output_path, "wb") as f:
                    f.write(video_bytes)
                print(f"\nSaved to: {output_path}")
            break

        elif status == "FAILED":
            print(f"Failed: {status_data.get('error')}")
            break

        elif elapsed > 600:  # 10 minute timeout
            print("Timeout: Job took too long")
            break

        time.sleep(10)


if __name__ == "__main__":
    test_render()
