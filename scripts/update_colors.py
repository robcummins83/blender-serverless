# Run this with: blender --background templates/ai_cpu_activation.blend --python scripts/update_colors.py -- --save
# Updates emission colors to match The Temperature Setting branding

import bpy
import sys

# Channel branding colors (linear RGB, not sRGB)
# Converting from hex to linear RGB (gamma 2.2)
def srgb_to_linear(c):
    """Convert sRGB value (0-1) to linear RGB"""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

# Branding colors in sRGB (0-1 range)
CYAN_SRGB = (0x4c/255, 0xc9/255, 0xf0/255)      # #4cc9f0
ORANGE_SRGB = (0xf7/255, 0x7f/255, 0x00/255)    # #f77f00
PINK_SRGB = (0xff/255, 0x00/255, 0x6e/255)      # #ff006e
GREEN_SRGB = (0x00/255, 0xd2/255, 0x6a/255)     # #00d26a

# Convert to linear RGB for Blender
CYAN = tuple(srgb_to_linear(c) for c in CYAN_SRGB) + (1.0,)
ORANGE = tuple(srgb_to_linear(c) for c in ORANGE_SRGB) + (1.0,)
PINK = tuple(srgb_to_linear(c) for c in PINK_SRGB) + (1.0,)
GREEN = tuple(srgb_to_linear(c) for c in GREEN_SRGB) + (1.0,)

print("\n" + "="*60)
print("UPDATING MATERIAL COLORS TO CHANNEL BRANDING")
print("="*60)
print(f"Cyan: {CYAN[:3]}")
print(f"Orange: {ORANGE[:3]}")
print(f"Pink: {PINK[:3]}")
print(f"Green: {GREEN[:3]}")
print("="*60)

# Color mapping - which materials get which color
# Based on the inspection, most are blue emissions - we'll make them cyan
# The green one (Material.005) stays green but uses our green
COLOR_MAP = {
    # Blue emissions -> Cyan (primary brand color)
    "Cube sifi": CYAN,
    "Curve circuit board": CYAN,
    "light trial on parth": CYAN,
    "Point_cube.Curve": CYAN,
    # Green -> Our brand green
    "Material.005": GREEN,
}

changes_made = 0

for mat in bpy.data.materials:
    if mat.name == "Logo_Material":
        print(f"SKIP: {mat.name} (logo, keep as-is)")
        continue

    if not mat.use_nodes:
        continue

    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            old_color = tuple(node.inputs['Color'].default_value)

            # Check if this material is in our map
            if mat.name in COLOR_MAP:
                new_color = COLOR_MAP[mat.name]
                node.inputs['Color'].default_value = new_color
                print(f"UPDATED: {mat.name}")
                print(f"  Old: ({old_color[0]:.2f}, {old_color[1]:.2f}, {old_color[2]:.2f})")
                print(f"  New: ({new_color[0]:.2f}, {new_color[1]:.2f}, {new_color[2]:.2f})")
                changes_made += 1
            else:
                # For any other emission materials, also convert blue-ish to cyan
                # Blue-ish = high blue component, low red
                if old_color[2] > 0.5 and old_color[0] < 0.3:
                    node.inputs['Color'].default_value = CYAN
                    print(f"UPDATED (auto): {mat.name}")
                    print(f"  Old: ({old_color[0]:.2f}, {old_color[1]:.2f}, {old_color[2]:.2f})")
                    print(f"  New: ({CYAN[0]:.2f}, {CYAN[1]:.2f}, {CYAN[2]:.2f})")
                    changes_made += 1
                else:
                    print(f"SKIP: {mat.name} - not in map and not blue-ish")

print("="*60)
print(f"Total changes: {changes_made}")
print("="*60)

# Check for --save argument
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        # Save the file
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
    else:
        print("Dry run - use --save to save changes")
else:
    print("Dry run - use --save to save changes")
