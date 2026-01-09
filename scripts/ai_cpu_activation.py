# Branding modifications for ai_cpu_activation.blend template
# Run: blender --background ai_cpu_activation.blend --python ai_cpu_activation.py -- --save
#
# This script applies all channel branding:
# - Replaces logo with "The Temperature Setting" text
# - Applies gradient text (cyan -> orange -> pink)
# - Updates all materials to branding colors
# - Updates all lights to branding colors

import bpy
import sys

# =============================================================================
# BRANDING COLORS (The Temperature Setting)
# =============================================================================
def srgb_to_linear(c):
    """Convert sRGB to linear color space for Blender."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

CYAN = tuple(srgb_to_linear(c) for c in (0x4c/255, 0xc9/255, 0xf0/255)) + (1.0,)
ORANGE = tuple(srgb_to_linear(c) for c in (0xf7/255, 0x7f/255, 0x00/255)) + (1.0,)
PINK = tuple(srgb_to_linear(c) for c in (0xff/255, 0x00/255, 0x6e/255)) + (1.0,)
GREEN = tuple(srgb_to_linear(c) for c in (0x00/255, 0xd2/255, 0x6a/255)) + (1.0,)
DARK_BG = tuple(srgb_to_linear(c) for c in (0x0a/255, 0x0f/255, 0x1a/255)) + (1.0,)

color_names = {id(CYAN): "CYAN", id(ORANGE): "ORANGE", id(PINK): "PINK", id(GREEN): "GREEN"}

print("\n" + "="*60)
print("AI_CPU_ACTIVATION BRANDING SCRIPT")
print("="*60)

# =============================================================================
# 1. HIDE ORIGINAL LOGO, ADD CHANNEL NAME TEXT
# =============================================================================
print("\n--- Setting up channel name text ---")

# Hide the logo plane
logo_plane = bpy.data.objects.get("Logo_Plane")
if logo_plane:
    logo_plane.hide_render = True
    logo_plane.hide_viewport = True
    print("Hidden Logo_Plane")

# Find original "AI" text for positioning reference
original_text = bpy.data.objects.get("Text.001")
if original_text:
    text_location = original_text.location.copy()
    text_rotation = original_text.rotation_euler.copy()
    text_parent = original_text.parent
    print(f"Found original text at: {text_location}, parent: {text_parent.name if text_parent else 'None'}")
else:
    text_location = (0, 0, 0.5)
    text_rotation = (0, 0, 0)
    text_parent = None
    print("Original text not found, using defaults")

# Check if channel name already exists
text_obj = bpy.data.objects.get("Channel_Name")
if not text_obj:
    # Create new text object
    bpy.ops.object.text_add()
    text_obj = bpy.context.active_object
    text_obj.name = "Channel_Name"
    text_obj.data.body = "The Temperature\nSetting"
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    text_obj.location = text_location
    text_obj.rotation_euler = text_rotation
    if text_parent:
        text_obj.parent = text_parent
        if original_text:
            text_obj.matrix_parent_inverse = original_text.matrix_parent_inverse.copy()
    print("Created Channel_Name text object")

# Set text size to fit within chip boundary
text_obj.data.size = 1.0
text_obj.scale = (0.05, 0.05, 0.05)
print(f"Text size: size=1.0, scale=0.05")

# =============================================================================
# 2. CREATE/UPDATE GRADIENT MATERIAL FOR TEXT
# =============================================================================
print("\n--- Setting up gradient text material ---")

mat = bpy.data.materials.get("Channel_Text_Material")
if not mat:
    mat = bpy.data.materials.new(name="Channel_Text_Material")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear and rebuild nodes
nodes.clear()

# Texture coordinate for gradient
tex_coord = nodes.new('ShaderNodeTexCoord')
tex_coord.location = (-600, 0)

# Separate XYZ to get horizontal position
separate = nodes.new('ShaderNodeSeparateXYZ')
separate.location = (-400, 0)

# Color ramp for gradient (cyan -> orange -> pink)
color_ramp = nodes.new('ShaderNodeValToRGB')
color_ramp.location = (-200, 0)
ramp = color_ramp.color_ramp
while len(ramp.elements) > 2:
    ramp.elements.remove(ramp.elements[1])
ramp.elements[0].position = 0.0
ramp.elements[0].color = CYAN
ramp.elements[1].position = 1.0
ramp.elements[1].color = PINK
middle = ramp.elements.new(0.5)
middle.color = ORANGE

# Emission node
emission = nodes.new('ShaderNodeEmission')
emission.location = (100, 0)
emission.inputs['Strength'].default_value = 8.0

# Output
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)

# Link nodes - use Object coordinates for proper gradient
links.new(tex_coord.outputs['Object'], separate.inputs['Vector'])
links.new(separate.outputs['X'], color_ramp.inputs['Fac'])
links.new(color_ramp.outputs['Color'], emission.inputs['Color'])
links.new(emission.outputs['Emission'], output.inputs['Surface'])

# Apply material to text
if text_obj.data.materials:
    text_obj.data.materials[0] = mat
else:
    text_obj.data.materials.append(mat)
print("Applied gradient material: CYAN -> ORANGE -> PINK")

# =============================================================================
# 3. UPDATE ALL OTHER MATERIALS TO BRANDING COLORS
# =============================================================================
print("\n--- Updating material colors ---")

color_cycle = [CYAN, CYAN, ORANGE, ORANGE, PINK, GREEN]
color_idx = 0

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    if mat.name == "Channel_Text_Material":
        continue

    for node in mat.node_tree.nodes:
        # Update emission nodes
        if node.type == 'EMISSION':
            new_color = color_cycle[color_idx % len(color_cycle)]
            node.inputs['Color'].default_value = new_color
            print(f"  {mat.name}: emission -> {color_names.get(id(new_color), 'unknown')}")
            color_idx += 1

        # Update color ramps to use branding colors
        elif node.type == 'VALTORGB':
            ramp = node.color_ramp
            elems = list(ramp.elements)
            if len(elems) >= 2:
                elems[0].color = CYAN
                elems[-1].color = PINK
                if len(elems) >= 3:
                    for elem in elems[1:-1]:
                        elem.color = ORANGE
                print(f"  {mat.name}: color ramp -> CYAN->ORANGE->PINK")

# =============================================================================
# 4. UPDATE ALL LIGHTS TO BRANDING COLORS
# =============================================================================
print("\n--- Updating lights ---")

light_colors = [CYAN[:3], ORANGE[:3], PINK[:3]]
light_idx = 0
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        obj.data.color = light_colors[light_idx % len(light_colors)]
        color_name = ["CYAN", "ORANGE", "PINK"][light_idx % 3]
        print(f"  {obj.name}: -> {color_name}")
        light_idx += 1

print("\n" + "="*60)
print("BRANDING COMPLETE")
print("="*60)

# =============================================================================
# SAVE IF REQUESTED
# =============================================================================
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
