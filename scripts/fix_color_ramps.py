# Fix color ramps to use branding colors
# Run: blender --background template.blend --python fix_color_ramps.py -- --save

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
BLACK = (0.0, 0.0, 0.0, 1.0)
WHITE = (1.0, 1.0, 1.0, 1.0)

print("\n" + "="*60)
print("FIXING COLOR RAMPS TO BRANDING COLORS")
print("="*60)

changes = 0

for mat in bpy.data.materials:
    if mat.name == "Channel_Text_Material":
        print(f"SKIP: {mat.name} (already branded)")
        continue

    if not mat.use_nodes:
        continue

    for node in mat.node_tree.nodes:
        if node.type == 'VALTORGB':  # Color Ramp
            updated = False

            for elem in node.color_ramp.elements:
                c = elem.color

                # Check if it's a blue-ish color (high blue, low red)
                if c[2] > 0.5 and c[0] < 0.5:
                    # Replace blue with cyan
                    elem.color = CYAN
                    updated = True

                # Check if it's purple (high blue and red, low green)
                elif c[0] > 0.3 and c[2] > 0.5 and c[1] < 0.3:
                    # Replace purple with pink
                    elem.color = PINK
                    updated = True

                # Check if it's red (high red, low others)
                elif c[0] > 0.7 and c[1] < 0.3 and c[2] < 0.3:
                    # Replace red with orange
                    elem.color = ORANGE
                    updated = True

                # Check if it's green (high green)
                elif c[1] > 0.7 and c[0] < 0.3 and c[2] < 0.5:
                    # Replace with brand green
                    elem.color = GREEN
                    updated = True

            if updated:
                print(f"UPDATED: {mat.name} color ramp")
                changes += 1

print(f"\n=== TOTAL CHANGES: {changes} ===")
print("="*60)

# Save if requested
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
