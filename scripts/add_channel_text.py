# Replace logo with "The Temperature Setting" text
# Run: blender --background template.blend --python add_channel_text.py -- --save

import bpy
import sys

print("\n" + "="*60)
print("ADDING CHANNEL NAME TEXT")
print("="*60)

# sRGB to linear conversion
def srgb_to_linear(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

# Branding cyan
CYAN = tuple(srgb_to_linear(c) for c in (0x4c/255, 0xc9/255, 0xf0/255)) + (1.0,)

# Find and hide the logo plane
logo_plane = bpy.data.objects.get("Logo_Plane")
if logo_plane:
    logo_plane.hide_render = True
    logo_plane.hide_viewport = True
    print("Hidden Logo_Plane")

# Find the original AI text to get its position and parent
original_text = bpy.data.objects.get("Text.001")
if original_text:
    text_location = original_text.location.copy()
    text_rotation = original_text.rotation_euler.copy()
    text_scale = original_text.scale.copy()
    text_parent = original_text.parent
    print(f"Found original text at: {text_location}")
    print(f"Parent: {text_parent.name if text_parent else 'None'}")
else:
    # Default position on chip
    text_location = (0, 0, 0.5)
    text_rotation = (0, 0, 0)
    text_scale = (1, 1, 1)
    text_parent = None
    print("Original text not found, using defaults")

# Create new text object
bpy.ops.object.text_add()
text_obj = bpy.context.active_object
text_obj.name = "Channel_Name"

# Set the text content
text_obj.data.body = "The Temperature\nSetting"
text_obj.data.align_x = 'CENTER'
text_obj.data.align_y = 'CENTER'

# Set font size (adjust as needed)
text_obj.data.size = 0.08  # Small size for chip

# Position it
text_obj.location = text_location
text_obj.rotation_euler = text_rotation
text_obj.scale = text_scale * 0.5  # Scale down

# Parent to same object as original text
if text_parent:
    text_obj.parent = text_parent
    text_obj.matrix_parent_inverse = original_text.matrix_parent_inverse.copy() if original_text else text_parent.matrix_world.inverted()
    print(f"Parented to: {text_parent.name}")

# Branding gradient colors
ORANGE = tuple(srgb_to_linear(c) for c in (0xf7/255, 0x7f/255, 0x00/255)) + (1.0,)
PINK = tuple(srgb_to_linear(c) for c in (0xff/255, 0x00/255, 0x6e/255)) + (1.0,)

# Create gradient emission material (cyan -> orange -> pink)
mat = bpy.data.materials.new(name="Channel_Text_Material")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear default nodes
nodes.clear()

# Texture coordinate for gradient
tex_coord = nodes.new('ShaderNodeTexCoord')
tex_coord.location = (-600, 0)

# Separate XYZ to get horizontal position
separate = nodes.new('ShaderNodeSeparateXYZ')
separate.location = (-400, 0)

# Color ramp for gradient
color_ramp = nodes.new('ShaderNodeValToRGB')
color_ramp.location = (-200, 0)
color_ramp.color_ramp.elements[0].position = 0.0
color_ramp.color_ramp.elements[0].color = CYAN
color_ramp.color_ramp.elements[1].position = 1.0
color_ramp.color_ramp.elements[1].color = PINK
# Add middle stop for orange
middle = color_ramp.color_ramp.elements.new(0.5)
middle.color = ORANGE

# Create emission node
emission = nodes.new('ShaderNodeEmission')
emission.location = (100, 0)
emission.inputs['Strength'].default_value = 8.0

# Create output
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)

# Link nodes
links.new(tex_coord.outputs['Generated'], separate.inputs['Vector'])
links.new(separate.outputs['X'], color_ramp.inputs['Fac'])
links.new(color_ramp.outputs['Color'], emission.inputs['Color'])
links.new(emission.outputs['Emission'], output.inputs['Surface'])

# Apply material
text_obj.data.materials.append(mat)

print(f"Created text object: {text_obj.name}")
print(f"Material color: CYAN {CYAN[:3]}")
print("="*60)

# Save if requested
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
