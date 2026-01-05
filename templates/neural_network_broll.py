"""
Blender B-Roll Generator - Neural Network Visualization
Proof of Concept for AI News Video Pipeline

Generates an animated 3D neural network with:
- Glowing nodes in layers
- Pulsing connections between nodes
- Camera movement
- Emission materials with bloom

Usage (headless):
    blender --background --python neural_network_broll.py -- --output /path/to/output.mp4

Usage (with GUI for preview):
    blender --python neural_network_broll.py
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
    # Network structure
    "layers": [4, 8, 12, 8, 4],  # Nodes per layer
    "layer_spacing": 3.0,        # Distance between layers
    "node_spacing": 1.2,         # Vertical spacing between nodes

    # Visual style
    "node_radius": 0.15,
    "connection_thickness": 0.02,
    "base_color": (0.0, 0.8, 1.0),      # Cyan
    "accent_color": (1.0, 0.4, 0.0),    # Orange
    "pulse_color": (0.0, 1.0, 0.5),     # Green

    # Animation
    "duration_seconds": 8,
    "fps": 30,
    "pulse_speed": 2.0,          # Pulses per second

    # Render settings
    "resolution_x": 1920,
    "resolution_y": 1080,
    "samples": 128,              # Cycles samples (higher = better quality)
    "use_gpu": True,

    # Output
    "output_path": "//neural_network_broll.mp4",
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clear_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Clear orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def create_emission_material(name, color, strength=5.0):
    """Create a glowing emission material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')

    # Set properties
    emission.inputs['Color'].default_value = (*color, 1.0)
    emission.inputs['Strength'].default_value = strength

    # Link nodes
    links.new(emission.outputs['Emission'], output.inputs['Surface'])

    # Position nodes
    output.location = (300, 0)
    emission.location = (0, 0)

    return mat


def create_animated_emission_material(name, color1, color2, speed=1.0):
    """Create emission material that pulses between two colors."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    # Nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    mix = nodes.new('ShaderNodeMixRGB')
    color_a = nodes.new('ShaderNodeRGB')
    color_b = nodes.new('ShaderNodeRGB')
    math_node = nodes.new('ShaderNodeMath')
    driver_value = nodes.new('ShaderNodeValue')

    # Set colors
    color_a.outputs[0].default_value = (*color1, 1.0)
    color_b.outputs[0].default_value = (*color2, 1.0)

    # Math for sine wave
    math_node.operation = 'SINE'

    # Set emission strength
    emission.inputs['Strength'].default_value = 8.0

    # Links
    links.new(driver_value.outputs[0], math_node.inputs[0])
    links.new(math_node.outputs[0], mix.inputs['Fac'])
    links.new(color_a.outputs[0], mix.inputs['Color1'])
    links.new(color_b.outputs[0], mix.inputs['Color2'])
    links.new(mix.outputs[0], emission.inputs['Color'])
    links.new(emission.outputs[0], output.inputs['Surface'])

    # Add driver for animation
    driver = driver_value.outputs[0].driver_add('default_value')
    driver.driver.expression = f"frame * {speed} * 0.1"

    return mat


# =============================================================================
# SCENE CREATION
# =============================================================================

def create_node(location, radius, material):
    """Create a single neural network node (sphere)."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius,
        segments=16,
        ring_count=8,
        location=location
    )
    node = bpy.context.active_object
    node.data.materials.append(material)

    # Smooth shading
    bpy.ops.object.shade_smooth()

    return node


def create_connection(start, end, thickness, material):
    """Create a connection (cylinder) between two points."""
    # Calculate midpoint and direction
    mid = (Vector(start) + Vector(end)) / 2
    direction = Vector(end) - Vector(start)
    length = direction.length

    # Create cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=thickness,
        depth=length,
        location=mid
    )
    conn = bpy.context.active_object

    # Rotate to align with direction
    conn.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

    conn.data.materials.append(material)

    return conn


def create_neural_network():
    """Create the full neural network visualization."""
    layers = CONFIG["layers"]
    layer_spacing = CONFIG["layer_spacing"]
    node_spacing = CONFIG["node_spacing"]
    node_radius = CONFIG["node_radius"]
    conn_thickness = CONFIG["connection_thickness"]

    # Materials
    node_mat = create_animated_emission_material(
        "NodeMaterial",
        CONFIG["base_color"],
        CONFIG["accent_color"],
        CONFIG["pulse_speed"]
    )

    conn_mat = create_emission_material(
        "ConnectionMaterial",
        (0.1, 0.3, 0.5),
        strength=2.0
    )

    # Store node positions for connections
    all_nodes = []
    node_positions = []

    # Create nodes layer by layer
    total_width = (len(layers) - 1) * layer_spacing
    start_x = -total_width / 2

    for layer_idx, num_nodes in enumerate(layers):
        layer_positions = []
        x = start_x + layer_idx * layer_spacing

        # Center nodes vertically
        total_height = (num_nodes - 1) * node_spacing
        start_z = -total_height / 2

        for node_idx in range(num_nodes):
            z = start_z + node_idx * node_spacing
            # Add slight random offset for organic feel
            y = random.uniform(-0.2, 0.2)

            pos = (x, y, z)
            node = create_node(pos, node_radius, node_mat)
            node.name = f"Node_L{layer_idx}_N{node_idx}"

            all_nodes.append(node)
            layer_positions.append(pos)

        node_positions.append(layer_positions)

    # Create connections between adjacent layers
    connections = []
    for layer_idx in range(len(layers) - 1):
        current_layer = node_positions[layer_idx]
        next_layer = node_positions[layer_idx + 1]

        for start_pos in current_layer:
            # Connect to random subset of next layer (not all, for cleaner look)
            num_connections = min(3, len(next_layer))
            targets = random.sample(next_layer, num_connections)

            for end_pos in targets:
                conn = create_connection(start_pos, end_pos, conn_thickness, conn_mat)
                conn.name = f"Conn_{layer_idx}"
                connections.append(conn)

    # Parent all to empty for easy manipulation
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    network_parent = bpy.context.active_object
    network_parent.name = "NeuralNetwork"

    for node in all_nodes:
        node.parent = network_parent
    for conn in connections:
        conn.parent = network_parent

    return network_parent, all_nodes, connections


def create_background():
    """Create dark background with subtle grid."""
    # World background
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes

    bg = nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.01, 0.02, 0.04, 1.0)
        bg.inputs['Strength'].default_value = 1.0

    # Add a subtle ground plane with grid texture
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, -5))
    ground = bpy.context.active_object
    ground.name = "Ground"

    # Grid material
    grid_mat = bpy.data.materials.new(name="GridMaterial")
    grid_mat.use_nodes = True
    nodes = grid_mat.node_tree.nodes
    links = grid_mat.node_tree.links

    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')

    emission.inputs['Color'].default_value = (0.0, 0.2, 0.4, 1.0)
    emission.inputs['Strength'].default_value = 0.5

    links.new(emission.outputs[0], output.inputs['Surface'])

    ground.data.materials.append(grid_mat)


def create_camera():
    """Create and animate the camera."""
    # Create camera
    bpy.ops.object.camera_add(location=(0, -15, 2))
    camera = bpy.context.active_object
    camera.name = "MainCamera"

    # Point at center
    camera.rotation_euler = (math.radians(80), 0, 0)

    # Set as active camera
    bpy.context.scene.camera = camera

    # Animate camera orbit
    total_frames = CONFIG["duration_seconds"] * CONFIG["fps"]

    # Create empty at center for camera to track
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    target = bpy.context.active_object
    target.name = "CameraTarget"

    # Add track constraint
    track = camera.constraints.new(type='TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    # Animate camera position (orbit)
    camera.location = (0, -15, 3)
    camera.keyframe_insert(data_path="location", frame=1)

    camera.location = (10, -10, 4)
    camera.keyframe_insert(data_path="location", frame=total_frames // 3)

    camera.location = (5, -12, 2)
    camera.keyframe_insert(data_path="location", frame=2 * total_frames // 3)

    camera.location = (0, -15, 3)
    camera.keyframe_insert(data_path="location", frame=total_frames)

    # Smooth interpolation
    for fcurve in camera.animation_data.action.fcurves:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = 'BEZIER'
            keyframe.handle_left_type = 'AUTO'
            keyframe.handle_right_type = 'AUTO'

    return camera


def create_lights():
    """Add dramatic lighting."""
    # Key light (cyan)
    bpy.ops.object.light_add(type='AREA', location=(5, -5, 8))
    key = bpy.context.active_object
    key.name = "KeyLight"
    key.data.energy = 500
    key.data.color = (0.7, 0.9, 1.0)
    key.data.size = 5

    # Fill light (orange)
    bpy.ops.object.light_add(type='AREA', location=(-5, -3, 4))
    fill = bpy.context.active_object
    fill.name = "FillLight"
    fill.data.energy = 200
    fill.data.color = (1.0, 0.6, 0.3)
    fill.data.size = 3

    # Rim light
    bpy.ops.object.light_add(type='AREA', location=(0, 5, 3))
    rim = bpy.context.active_object
    rim.name = "RimLight"
    rim.data.energy = 300
    rim.data.color = (0.5, 0.7, 1.0)
    rim.data.size = 8


# =============================================================================
# RENDER SETTINGS
# =============================================================================

def setup_render():
    """Configure render settings for high quality output."""
    scene = bpy.context.scene

    # Frame range
    scene.frame_start = 1
    scene.frame_end = CONFIG["duration_seconds"] * CONFIG["fps"]
    scene.frame_current = 1

    # Render engine
    scene.render.engine = 'CYCLES'

    # GPU setup - try multiple backends
    gpu_enabled = False
    if CONFIG["use_gpu"]:
        prefs = bpy.context.preferences.addons['cycles'].preferences

        # Try different compute backends in order of preference
        for device_type in ['OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL']:
            try:
                prefs.compute_device_type = device_type
                prefs.get_devices()

                # Check if any GPU devices are available
                gpu_devices = [d for d in prefs.devices if d.type != 'CPU']

                if gpu_devices:
                    print(f"Found {len(gpu_devices)} GPU(s) with {device_type}:")
                    for device in prefs.devices:
                        device.use = (device.type != 'CPU')  # Enable GPUs, disable CPU
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
    else:
        scene.cycles.device = 'CPU'
        print("GPU disabled in config, using CPU")

    # Quality - reduce if CPU
    if gpu_enabled:
        scene.cycles.samples = CONFIG["samples"]
    else:
        scene.cycles.samples = min(CONFIG["samples"], 32)  # Lower samples for CPU
        print(f"Reduced samples to {scene.cycles.samples} for CPU rendering")

    scene.cycles.use_denoising = True

    # Resolution
    scene.render.resolution_x = CONFIG["resolution_x"]
    scene.render.resolution_y = CONFIG["resolution_y"]
    scene.render.resolution_percentage = 100

    # Output format
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.ffmpeg.ffmpeg_preset = 'GOOD'

    scene.render.filepath = CONFIG["output_path"]

    # Bloom/Glare in compositor
    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links

    nodes.clear()

    render_layers = nodes.new('CompositorNodeRLayers')
    glare = nodes.new('CompositorNodeGlare')
    composite = nodes.new('CompositorNodeComposite')

    glare.glare_type = 'FOG_GLOW'
    glare.threshold = 0.5
    glare.size = 7

    links.new(render_layers.outputs['Image'], glare.inputs['Image'])
    links.new(glare.outputs['Image'], composite.inputs['Image'])

    # Position nodes
    render_layers.location = (0, 0)
    glare.location = (300, 0)
    composite.location = (600, 0)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main function to generate the B-roll."""
    print("=" * 60)
    print("Blender B-Roll Generator - Neural Network")
    print("=" * 60)

    # Parse command line args for output path
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        for i, arg in enumerate(args):
            if arg == "--output" and i + 1 < len(args):
                CONFIG["output_path"] = args[i + 1]

    print(f"\nOutput: {CONFIG['output_path']}")
    print(f"Resolution: {CONFIG['resolution_x']}x{CONFIG['resolution_y']}")
    print(f"Duration: {CONFIG['duration_seconds']}s @ {CONFIG['fps']}fps")
    print(f"Frames: {CONFIG['duration_seconds'] * CONFIG['fps']}")

    # Build scene
    print("\n[1/6] Clearing scene...")
    clear_scene()

    print("[2/6] Creating neural network...")
    network, nodes, connections = create_neural_network()
    print(f"       Created {len(nodes)} nodes, {len(connections)} connections")

    print("[3/6] Creating background...")
    create_background()

    print("[4/6] Setting up camera...")
    camera = create_camera()

    print("[5/6] Adding lights...")
    create_lights()

    print("[6/6] Configuring render settings...")
    setup_render()

    print("\n" + "=" * 60)
    print("Scene ready!")
    print("=" * 60)

    # Check if running in background mode
    if bpy.app.background:
        print("\nStarting render...")
        bpy.ops.render.render(animation=True)
        print(f"\nRender complete! Output: {CONFIG['output_path']}")
    else:
        print("\nRunning in GUI mode - use Render > Render Animation to render")
        print("Or run with: blender --background --python neural_network_broll.py")


if __name__ == "__main__":
    main()
