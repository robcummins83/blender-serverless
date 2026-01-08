"""
Render a .blend file with customizable settings.

Usage:
    blender --background template.blend --python render_blend.py -- \
        --output /path/to/output.mp4 \
        --duration 8 \
        --samples 128

This script:
1. Loads the .blend file (passed to blender via command line)
2. Configures render settings (GPU, resolution, samples)
3. Adjusts animation length if duration specified
4. Renders to MP4
"""

import bpy
import sys
import math
import subprocess
import tempfile
import shutil
import os


def parse_args():
    """Parse command line arguments after '--'."""
    args = {
        "output": "/tmp/output.mp4",
        "duration": None,  # None = use file's existing duration
        "width": 1920,
        "height": 1080,
        "samples": 128,
        "fps": 30,
    }

    argv = sys.argv
    if "--" in argv:
        custom_args = argv[argv.index("--") + 1:]
        i = 0
        while i < len(custom_args):
            if custom_args[i] == "--output" and i + 1 < len(custom_args):
                args["output"] = custom_args[i + 1]
                i += 2
            elif custom_args[i] == "--duration" and i + 1 < len(custom_args):
                args["duration"] = int(custom_args[i + 1])
                i += 2
            elif custom_args[i] == "--width" and i + 1 < len(custom_args):
                args["width"] = int(custom_args[i + 1])
                i += 2
            elif custom_args[i] == "--height" and i + 1 < len(custom_args):
                args["height"] = int(custom_args[i + 1])
                i += 2
            elif custom_args[i] == "--samples" and i + 1 < len(custom_args):
                args["samples"] = int(custom_args[i + 1])
                i += 2
            elif custom_args[i] == "--fps" and i + 1 < len(custom_args):
                args["fps"] = int(custom_args[i + 1])
                i += 2
            else:
                i += 1

    return args


def setup_gpu(require_gpu=True):
    """Configure GPU rendering.

    Args:
        require_gpu: If True, raise error if no GPU found (default True for RunPod)

    Reference: https://github.com/nytimes/rd-blender-docker/issues/3
    """
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'

    prefs = bpy.context.preferences.addons['cycles'].preferences
    gpu_enabled = False

    # CRITICAL: Call get_devices() FIRST to populate the device list
    print("Detecting GPU devices...")
    try:
        cuda_devices, opencl_devices = prefs.get_devices()
        print(f"  CUDA devices: {len(cuda_devices) if cuda_devices else 0}")
        print(f"  OpenCL devices: {len(opencl_devices) if opencl_devices else 0}")
    except Exception as e:
        print(f"  get_devices() returned: {e}")

    # Try OptiX FIRST - uses RT cores, 2-3x faster on RTX cards
    for device_type in ['OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL']:
        try:
            print(f"Trying {device_type}...")
            prefs.compute_device_type = device_type

            gpu_devices = [d for d in prefs.devices if d.type != 'CPU']
            print(f"  Found {len(gpu_devices)} GPU device(s)")

            if gpu_devices:
                print(f"Enabling {len(gpu_devices)} GPU(s) with {device_type}:")
                # Enable ALL devices
                for device in prefs.devices:
                    device.use = True
                    print(f"  - {device.name} ({device.type}): enabled")

                # Set GPU for ALL scenes
                for s in bpy.data.scenes:
                    s.cycles.device = 'GPU'

                gpu_enabled = True
                print(f"GPU rendering ENABLED with {device_type}")
                break

        except TypeError as e:
            print(f"{device_type} not supported: {e}")
            continue
        except Exception as e:
            print(f"{device_type} error: {e}")
            continue

    if not gpu_enabled:
        if require_gpu:
            raise RuntimeError("ERROR: No GPU found! GPU is required for rendering.")
        else:
            print("WARNING: No GPU found, falling back to CPU (will be slow)")
            scene.cycles.device = 'CPU'

    return gpu_enabled


def setup_render(args, gpu_enabled):
    """Configure render settings."""
    scene = bpy.context.scene

    # Resolution
    scene.render.resolution_x = args["width"]
    scene.render.resolution_y = args["height"]
    scene.render.resolution_percentage = 100

    # FPS
    scene.render.fps = args["fps"]

    # Duration - adjust frame range if specified
    if args["duration"]:
        total_frames = args["duration"] * args["fps"]
        scene.frame_start = 1
        scene.frame_end = total_frames
        print(f"Set duration to {args['duration']}s ({total_frames} frames)")
    else:
        # Use existing animation range
        total_frames = scene.frame_end - scene.frame_start + 1
        duration = total_frames / scene.render.fps
        print(f"Using existing duration: {duration:.1f}s ({total_frames} frames)")

    # Samples - reduce for CPU
    if gpu_enabled:
        scene.cycles.samples = args["samples"]
    else:
        scene.cycles.samples = min(args["samples"], 32)
        print(f"Reduced samples to {scene.cycles.samples} for CPU")

    scene.cycles.use_denoising = True

    # Output format - PNG frames (encode with NVENC after)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'


def main():
    print("=" * 60)
    print("Blender .blend File Renderer")
    print("=" * 60)

    args = parse_args()

    print(f"\nSettings:")
    print(f"  Output: {args['output']}")
    print(f"  Resolution: {args['width']}x{args['height']}")
    print(f"  Samples: {args['samples']}")
    print(f"  FPS: {args['fps']}")
    if args['duration']:
        print(f"  Duration: {args['duration']}s (override)")
    else:
        print(f"  Duration: (using file default)")

    # Setup GPU
    print("\n[1/3] Configuring GPU...")
    gpu_enabled = setup_gpu()

    # Setup render settings
    print("\n[2/3] Configuring render...")
    setup_render(args, gpu_enabled)

    # Render to PNG frames
    print("\n[3/3] Rendering...")
    print("=" * 60)

    frames_dir = tempfile.mkdtemp(prefix="blender_frames_")
    scene = bpy.context.scene
    scene.render.filepath = os.path.join(frames_dir, "frame_")

    print(f"Rendering {scene.frame_end} frames to: {frames_dir}")
    bpy.ops.render.render(animation=True)

    # Encode with NVENC (GPU-accelerated H264)
    print("\n[4/4] Encoding with NVENC...")
    output_path = args["output"]
    fps = args["fps"]

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-hwaccel", "cuda",
        "-hwaccel_output_format", "cuda",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%04d.png"),
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-cq", "23",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print(f"Running: {' '.join(ffmpeg_cmd)}")
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"NVENC failed: {result.stderr}")
        print("Falling back to CPU encoding...")
        ffmpeg_fallback = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", os.path.join(frames_dir, "frame_%04d.png"),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        subprocess.run(ffmpeg_fallback, capture_output=True, text=True)

    # Cleanup frames
    shutil.rmtree(frames_dir)

    print("=" * 60)
    print(f"Render complete! Output: {output_path}")


if __name__ == "__main__":
    main()
