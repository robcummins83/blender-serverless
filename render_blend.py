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
    """
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'

    prefs = bpy.context.preferences.addons['cycles'].preferences
    gpu_enabled = False

    # Try OptiX FIRST - uses RT cores, 2-3x faster on RTX cards
    for device_type in ['OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL']:
        try:
            print(f"Trying {device_type}...")
            prefs.compute_device_type = device_type
            prefs.get_devices()  # Refresh device list

            gpu_devices = [d for d in prefs.devices if d.type != 'CPU']

            if gpu_devices:
                print(f"Found {len(gpu_devices)} GPU(s) with {device_type}:")
                for device in prefs.devices:
                    device.use = (device.type != 'CPU')
                    status = 'enabled' if device.use else 'disabled'
                    print(f"  - {device.name} ({device.type}): {status}")

                scene.cycles.device = 'GPU'
                gpu_enabled = True
                print(f"GPU rendering ENABLED with {device_type}")
                break

        except Exception as e:
            print(f"{device_type} not available: {e}")
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

    # Output format - MP4
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.ffmpeg.ffmpeg_preset = 'GOOD'

    scene.render.filepath = args["output"]


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

    # Render
    print("\n[3/3] Rendering...")
    print("=" * 60)

    bpy.ops.render.render(animation=True)

    print("=" * 60)
    print(f"Render complete! Output: {args['output']}")


if __name__ == "__main__":
    main()
