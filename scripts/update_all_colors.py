# Update ALL color sources to branding colors
# Run: blender --background template.blend --python update_all_colors.py -- --save

import bpy
import sys

# sRGB to linear conversion
def srgb_to_linear(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

# Branding colors (linear RGB)
CYAN = tuple(srgb_to_linear(c) for c in (0x4c/255, 0xc9/255, 0xf0/255)) + (1.0,)
ORANGE = tuple(srgb_to_linear(c) for c in (0xf7/255, 0x7f/255, 0x00/255)) + (1.0,)
PINK = tuple(srgb_to_linear(c) for c in (0xff/255, 0x00/255, 0x6e/255)) + (1.0,)
GREEN = tuple(srgb_to_linear(c) for c in (0x00/255, 0xd2/255, 0x6a/255)) + (1.0,)

print("\n" + "="*60)
print("UPDATING ALL COLORS TO BRANDING")
print("="*60)
print(f"Cyan: {CYAN[:3]}")
print(f"Orange: {ORANGE[:3]}")
print(f"Pink: {PINK[:3]}")
print(f"Green: {GREEN[:3]}")

changes = 0

# 1. Update LIGHTS
print("\n=== UPDATING LIGHTS ===")
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        light = obj.data
        old_color = tuple(light.color)
        # If it's blue-ish, change to cyan
        if old_color[2] > 0.5 and old_color[0] < 0.3:
            light.color = CYAN[:3]
            print(f"UPDATED {obj.name}: ({old_color[0]:.2f}, {old_color[1]:.2f}, {old_color[2]:.2f}) -> CYAN")
            changes += 1
        else:
            print(f"SKIP {obj.name}: ({old_color[0]:.2f}, {old_color[1]:.2f}, {old_color[2]:.2f})")

# 2. Update emission materials (in case any were missed)
print("\n=== UPDATING EMISSION MATERIALS ===")
for mat in bpy.data.materials:
    if mat.name == "Logo_Material":
        print(f"SKIP: {mat.name} (logo)")
        continue

    if not mat.use_nodes:
        continue

    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            old_color = tuple(node.inputs['Color'].default_value)
            # If blue-ish, change to cyan
            if old_color[2] > 0.5 and old_color[0] < 0.2:
                node.inputs['Color'].default_value = CYAN
                print(f"UPDATED {mat.name}: blue -> CYAN")
                changes += 1
            # If green, use our brand green
            elif old_color[1] > 0.5 and old_color[0] < 0.2 and old_color[2] < 0.5:
                node.inputs['Color'].default_value = GREEN
                print(f"UPDATED {mat.name}: green -> BRAND GREEN")
                changes += 1
            else:
                print(f"SKIP {mat.name}: already branded or other color")

print(f"\n=== TOTAL CHANGES: {changes} ===")
print("="*60)

# Save if requested
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
