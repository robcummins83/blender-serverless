# Fix text size to match original "AI" text width and apply proper branding colors
# Run: blender --background template.blend --python adjust_text_and_colors.py -- --save

import bpy
import sys

# sRGB to linear conversion
def srgb_to_linear(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

# Branding colors (The Temperature Setting)
CYAN = tuple(srgb_to_linear(c) for c in (0x4c/255, 0xc9/255, 0xf0/255)) + (1.0,)
ORANGE = tuple(srgb_to_linear(c) for c in (0xf7/255, 0x7f/255, 0x00/255)) + (1.0,)
PINK = tuple(srgb_to_linear(c) for c in (0xff/255, 0x00/255, 0x6e/255)) + (1.0,)
GREEN = tuple(srgb_to_linear(c) for c in (0x00/255, 0xd2/255, 0x6a/255)) + (1.0,)
DARK_BG = tuple(srgb_to_linear(c) for c in (0x0a/255, 0x0f/255, 0x1a/255)) + (1.0,)

print("\n" + "="*60)
print("ADJUSTING TEXT SIZE AND COLOR BALANCE")
print("="*60)

# 1. Fix text size to match original "AI" text width
text_obj = bpy.data.objects.get("Channel_Name")
if text_obj:
    # Match original "AI" text (Text.001) which uses size=1.0, scale=0.233
    # Scale down to fit within chip boundary
    text_obj.data.size = 1.0
    text_obj.scale = (0.05, 0.05, 0.05)
    print(f"Text size fixed: size=1.0, scale=0.05")

    # 2. Fix the gradient material to use proper coordinates
    mat = text_obj.data.materials[0] if text_obj.data.materials else None
    if mat and mat.use_nodes:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Find tex_coord and separate nodes
        tex_coord = None
        separate = None
        color_ramp = None

        for node in nodes:
            if node.type == 'TEX_COORD':
                tex_coord = node
            elif node.type == 'SEPARATE_XYZ':
                separate = node
            elif node.type == 'VALTORGB':
                color_ramp = node

        # Fix: Use Object coordinates instead of Generated for better gradient control
        if tex_coord and separate:
            # Remove old link
            for link in list(mat.node_tree.links):
                if link.to_node == separate and link.to_socket.name == 'Vector':
                    links.remove(link)
            # Use Object coordinates
            links.new(tex_coord.outputs['Object'], separate.inputs['Vector'])
            print("Fixed gradient to use Object coordinates")

        # Ensure color ramp has correct gradient: cyan -> orange -> pink
        if color_ramp:
            ramp = color_ramp.color_ramp
            # Clear and recreate elements
            while len(ramp.elements) > 2:
                ramp.elements.remove(ramp.elements[1])
            ramp.elements[0].position = 0.0
            ramp.elements[0].color = CYAN
            ramp.elements[1].position = 1.0
            ramp.elements[1].color = PINK
            # Add orange in middle
            middle = ramp.elements.new(0.5)
            middle.color = ORANGE
            print("Fixed gradient colors: CYAN -> ORANGE -> PINK")
else:
    print("WARNING: Channel_Name not found")

# 3. Apply branding colors comprehensively to all emissive materials
# Distribute colors: ~40% cyan (primary), ~30% orange, ~20% pink, ~10% green
color_cycle = [CYAN, CYAN, ORANGE, ORANGE, PINK, GREEN]
color_names = {id(CYAN): "CYAN", id(ORANGE): "ORANGE", id(PINK): "PINK", id(GREEN): "GREEN"}
color_idx = 0

print("\n--- Updating material colors ---")
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue

    # Skip the channel text material (already has gradient)
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
                # Use cyan->pink gradient for color ramps
                elems[0].color = CYAN
                elems[-1].color = PINK
                # Add orange in middle if there are middle elements
                if len(elems) >= 3:
                    for elem in elems[1:-1]:
                        elem.color = ORANGE
                print(f"  {mat.name}: color ramp -> CYAN->ORANGE->PINK")

# 4. Update all lights to branding colors
print("\n--- Updating lights ---")
light_colors = [CYAN[:3], ORANGE[:3], PINK[:3]]
light_idx = 0
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        obj.data.color = light_colors[light_idx % len(light_colors)]
        color_name = ["CYAN", "ORANGE", "PINK"][light_idx % 3]
        print(f"  {obj.name}: -> {color_name}")
        light_idx += 1

print("="*60)

# Save if requested
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
