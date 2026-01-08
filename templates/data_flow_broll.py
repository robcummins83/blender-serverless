"""
Blender B-Roll Generator - Data Flow Visualization
Abstract particles flowing along paths with glowing trails

Usage (headless):
    blender --background --python data_flow_broll.py -- --output /path/to/output.mp4
"""

import bpy
import math
import random
import sys
from mathutils import Vector

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    # Flow paths
    "num_paths": 8,
    "path_length": 20,
    "path_spread": 6.0,

    # Particles
    "particles_per_path": 30,
    "particle_size": 0.08,

    # Visual style
    "primary_color": (0.0, 0.9, 1.0),    # Cyan
    "secondary_color": (1.0, 0.3, 0.6),  # Pink
    "trail_color": (0.2, 0.4, 0.8),      # Blue

    # Animation
    "duration_seconds": 8,
    "fps": 30,
    "flow_speed": 0.15,

    # Render
    "resolution_x": 1920,
    "resolution_y": 1080,
    "samples": 64,
    "use_gpu": True,
    "output_path": "//data_flow_broll.mp4",
}


def clear_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.curves:
        if block.users == 0:
            bpy.data.curves.remove(block)


def create_emission_material(name, color, strength=10.0):
    """Create glowing emission material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*color, 1.0)
    emission.inputs['Strength'].default_value = strength
    links.new(emission.outputs[0], output.inputs['Surface'])

    return mat


def create_flow_path(start_pos, direction, length, curvature=0.3):
    """Create a curved bezier path for particles to follow."""
    # Create curve data
    curve_data = bpy.data.curves.new(name="FlowPath", type='CURVE')
    curve_data.dimensions = '3D'

    # Create spline
    spline = curve_data.splines.new('BEZIER')
    num_points = 5
    spline.bezier_points.add(num_points - 1)

    # Generate curved path
    for i, point in enumerate(spline.bezier_points):
        t = i / (num_points - 1)
        x = start_pos[0] + direction[0] * length * t
        y = start_pos[1] + direction[1] * length * t
        z = start_pos[2] + math.sin(t * math.pi * 2) * curvature

        # Add some random variation
        x += random.uniform(-0.5, 0.5)
        y += random.uniform(-0.5, 0.5)

        point.co = (x, y, z)
        point.handle_type_left = 'AUTO'
        point.handle_type_right = 'AUTO'

    # Create object
    curve_obj = bpy.data.objects.new("FlowPath", curve_data)
    bpy.context.collection.objects.link(curve_obj)

    return curve_obj


def create_particle_on_path(path_obj, offset, material, size):
    """Create a particle (icosphere) that follows a path."""
    # Create particle
    bpy.ops.mesh.primitive_ico_sphere_add(
        radius=size,
        subdivisions=2,
        location=(0, 0, 0)
    )
    particle = bpy.context.active_object
    particle.data.materials.append(material)
    bpy.ops.object.shade_smooth()

    # Add follow path constraint
    constraint = particle.constraints.new(type='FOLLOW_PATH')
    constraint.target = path_obj
    constraint.use_fixed_location = True
    constraint.offset_factor = offset

    # Animate along path
    total_frames = CONFIG["duration_seconds"] * CONFIG["fps"]

    # Start position (with offset so particles are staggered)
    start_offset = offset
    constraint.offset_factor = start_offset
    constraint.keyframe_insert(data_path="offset_factor", frame=1)

    # End position (loop around)
    end_offset = start_offset + CONFIG["flow_speed"] * CONFIG["duration_seconds"]
    constraint.offset_factor = end_offset
    constraint.keyframe_insert(data_path="offset_factor", frame=total_frames)

    # Linear interpolation for constant speed
    if particle.animation_data and particle.animation_data.action:
        for fcurve in particle.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'

    return particle


def create_data_flow():
    """Create the full data flow visualization."""
    num_paths = CONFIG["num_paths"]
    particles_per_path = CONFIG["particles_per_path"]

    # Materials with color gradient
    materials = []
    for i in range(num_paths):
        t = i / max(1, num_paths - 1)
        color = (
            CONFIG["primary_color"][0] * (1 - t) + CONFIG["secondary_color"][0] * t,
            CONFIG["primary_color"][1] * (1 - t) + CONFIG["secondary_color"][1] * t,
            CONFIG["primary_color"][2] * (1 - t) + CONFIG["secondary_color"][2] * t,
        )
        mat = create_emission_material(f"FlowMat_{i}", color, strength=15.0)
        materials.append(mat)

    all_objects = []

    # Create converging paths (like data flowing to a central point)
    for i in range(num_paths):
        angle = (i / num_paths) * math.pi * 2
        spread = CONFIG["path_spread"]

        # Start from outer ring, flow toward center
        start_x = math.cos(angle) * spread
        start_y = -CONFIG["path_length"] / 2
        start_z = math.sin(angle) * spread * 0.5

        # Direction toward center
        direction = (-start_x / CONFIG["path_length"], 1, -start_z / CONFIG["path_length"])

        # Create path
        path = create_flow_path(
            (start_x, start_y, start_z),
            direction,
            CONFIG["path_length"],
            curvature=random.uniform(0.2, 0.5)
        )
        path.name = f"Path_{i}"
        all_objects.append(path)

        # Create particles on path
        mat = materials[i]
        for j in range(particles_per_path):
            offset = j / particles_per_path
            particle = create_particle_on_path(
                path,
                offset,
                mat,
                CONFIG["particle_size"] * random.uniform(0.7, 1.3)
            )
            particle.name = f"Particle_{i}_{j}"
            all_objects.append(particle)

    # Create central destination sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.5,
        segments=32,
        ring_count=16,
        location=(0, CONFIG["path_length"] / 2 - 2, 0)
    )
    center = bpy.context.active_object
    center.name = "CentralNode"
    center_mat = create_emission_material("CenterMat", CONFIG["primary_color"], strength=20.0)
    center.data.materials.append(center_mat)
    bpy.ops.object.shade_smooth()

    # Animate central node pulsing (scale)
    total_frames = CONFIG["duration_seconds"] * CONFIG["fps"]
    for frame in range(1, total_frames + 1, 15):
        scale = 1.0 + 0.2 * math.sin(frame * 0.2)
        center.scale = (scale, scale, scale)
        center.keyframe_insert(data_path="scale", frame=frame)

    all_objects.append(center)

    return all_objects


def create_background():
    """Dark blue gradient background."""
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    nodes.clear()

    output = nodes.new('ShaderNodeOutputWorld')
    background = nodes.new('ShaderNodeBackground')
    gradient = nodes.new('ShaderNodeTexGradient')
    mapping = nodes.new('ShaderNodeMapping')
    tex_coord = nodes.new('ShaderNodeTexCoord')
    color_ramp = nodes.new('ShaderNodeValToRGB')

    # Dark gradient
    color_ramp.color_ramp.elements[0].color = (0.0, 0.01, 0.03, 1.0)
    color_ramp.color_ramp.elements[1].color = (0.02, 0.05, 0.1, 1.0)

    background.inputs['Strength'].default_value = 1.0

    # Links
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], gradient.inputs['Vector'])
    links.new(gradient.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], background.inputs['Color'])
    links.new(background.outputs['Background'], output.inputs['Surface'])


def create_camera():
    """Create animated camera."""
    bpy.ops.object.camera_add(location=(8, -8, 5))
    camera = bpy.context.active_object
    camera.name = "MainCamera"
    bpy.context.scene.camera = camera

    # Track to center
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 2, 0))
    target = bpy.context.active_object
    target.name = "CameraTarget"

    track = camera.constraints.new(type='TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    # Animate
    total_frames = CONFIG["duration_seconds"] * CONFIG["fps"]

    camera.location = (8, -8, 5)
    camera.keyframe_insert(data_path="location", frame=1)

    camera.location = (-6, -6, 3)
    camera.keyframe_insert(data_path="location", frame=total_frames // 2)

    camera.location = (8, -8, 5)
    camera.keyframe_insert(data_path="location", frame=total_frames)

    # Smooth
    for fcurve in camera.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'BEZIER'
            kf.handle_left_type = 'AUTO'
            kf.handle_right_type = 'AUTO'

    return camera


def setup_render():
    """Configure render settings."""
    scene = bpy.context.scene

    scene.frame_start = 1
    scene.frame_end = CONFIG["duration_seconds"] * CONFIG["fps"]

    scene.render.engine = 'CYCLES'

    # GPU setup - try multiple backends
    gpu_enabled = False
    if CONFIG["use_gpu"]:
        prefs = bpy.context.preferences.addons['cycles'].preferences

        # Try different compute backends in order of preference
        for device_type in ['CUDA', 'OPTIX', 'HIP', 'ONEAPI', 'METAL']:
            try:
                print(f"Trying {device_type}...")
                prefs.compute_device_type = device_type

                # Refresh device list after setting compute type
                prefs.get_devices()

                gpu_devices = [d for d in prefs.devices if d.type != 'CPU']
                print(f"  Found {len(gpu_devices)} GPU device(s), {len(prefs.devices)} total devices")

                if gpu_devices:
                    print(f"Found {len(gpu_devices)} GPU(s) with {device_type}:")
                    for device in prefs.devices:
                        device.use = (device.type != 'CPU')
                        print(f"  - {device.name} ({device.type}): {'enabled' if device.use else 'disabled'}")

                    scene.cycles.device = 'GPU'
                    gpu_enabled = True
                    print(f"GPU rendering enabled with {device_type}")
                    break

            except Exception as e:
                print(f"{device_type} not available: {e}")
                continue

        if not gpu_enabled:
            print("WARNING: No GPU found, falling back to CPU rendering")
            scene.cycles.device = 'CPU'

    scene.cycles.samples = CONFIG["samples"]
    scene.cycles.use_denoising = True

    scene.render.resolution_x = CONFIG["resolution_x"]
    scene.render.resolution_y = CONFIG["resolution_y"]
    scene.render.resolution_percentage = 100

    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'

    scene.render.filepath = CONFIG["output_path"]

    # Glare compositor
    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    rl = nodes.new('CompositorNodeRLayers')
    glare = nodes.new('CompositorNodeGlare')
    comp = nodes.new('CompositorNodeComposite')

    glare.glare_type = 'FOG_GLOW'
    glare.threshold = 0.3
    glare.size = 8

    links.new(rl.outputs['Image'], glare.inputs['Image'])
    links.new(glare.outputs['Image'], comp.inputs['Image'])


def main():
    print("=" * 60)
    print("Blender B-Roll Generator - Data Flow")
    print("=" * 60)

    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        for i, arg in enumerate(args):
            if arg == "--output" and i + 1 < len(args):
                CONFIG["output_path"] = args[i + 1]

    print(f"\nOutput: {CONFIG['output_path']}")

    print("\n[1/5] Clearing scene...")
    clear_scene()

    print("[2/5] Creating data flow...")
    objects = create_data_flow()
    print(f"       Created {len(objects)} objects")

    print("[3/5] Creating background...")
    create_background()

    print("[4/5] Setting up camera...")
    create_camera()

    print("[5/5] Configuring render...")
    setup_render()

    print("\nScene ready!")

    if bpy.app.background:
        print("\nStarting render...")
        bpy.ops.render.render(animation=True)
        print(f"\nComplete! Output: {CONFIG['output_path']}")
    else:
        print("\nGUI mode - render manually or run headless")


if __name__ == "__main__":
    main()
