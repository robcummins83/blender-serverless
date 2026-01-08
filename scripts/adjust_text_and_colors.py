# Make text bigger and balance colors (less cyan dominance)
# Run: blender --background template.blend --python adjust_text_and_colors.py -- --save

import bpy
import sys

# sRGB to linear conversion
def srgb_to_linear(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

# Branding colors
CYAN = tuple(srgb_to_linear(c) for c in (0x4c/255, 0xc9/255, 0xf0/255)) + (1.0,)
ORANGE = tuple(srgb_to_linear(c) for c in (0xf7/255, 0x7f/255, 0x00/255)) + (1.0,)
PINK = tuple(srgb_to_linear(c) for c in (0xff/255, 0x00/255, 0x6e/255)) + (1.0,)
GREEN = tuple(srgb_to_linear(c) for c in (0x00/255, 0xd2/255, 0x6a/255)) + (1.0,)

print("\n" + "="*60)
print("ADJUSTING TEXT SIZE AND COLOR BALANCE")
print("="*60)

# 1. Make text bigger
text_obj = bpy.data.objects.get("Channel_Name")
if text_obj:
    # Increase font size
    text_obj.data.size = 0.15  # Was 0.08
    # Increase scale
    text_obj.scale = (1.0, 1.0, 1.0)  # Was 0.5
    print(f"Text size increased: size=0.15, scale=1.0")
else:
    print("WARNING: Channel_Name not found")

# 2. Balance colors - change some cyan elements to orange/pink
# Change specific materials to add variety
color_assignments = {
    # Light trails - mix of colors
    "light trial on parth": ORANGE,  # Change from cyan to orange
    "Curve.sci fi": PINK,            # Change to pink
    # Keep some cyan
    "Curve circuit board": CYAN,
    "Point_cube.Curve": CYAN,
    # Material.071 - make it orange/pink gradient
    "Material.071": ORANGE,
}

for mat in bpy.data.materials:
    if mat.name in color_assignments:
        if not mat.use_nodes:
            continue
        new_color = color_assignments[mat.name]
        for node in mat.node_tree.nodes:
            if node.type == 'EMISSION':
                node.inputs['Color'].default_value = new_color
                print(f"Changed {mat.name} emission to {['CYAN','ORANGE','PINK','GREEN'][[CYAN,ORANGE,PINK,GREEN].index(new_color)] if new_color in [CYAN,ORANGE,PINK,GREEN] else 'custom'}")

# 3. Update color ramps for variety
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'VALTORGB':
            if mat.name == "light trial on parth":
                # Orange trail
                for elem in node.color_ramp.elements:
                    if elem.color[0] > 0.01 or elem.color[1] > 0.01 or elem.color[2] > 0.01:
                        if elem.color[3] > 0.5:  # Not black
                            elem.color = ORANGE
                print(f"Updated {mat.name} color ramp to ORANGE")
            elif mat.name == "Curve.sci fi":
                # Pink trail
                for elem in node.color_ramp.elements:
                    if elem.color[0] > 0.01 or elem.color[1] > 0.01 or elem.color[2] > 0.01:
                        if elem.color[3] > 0.5:
                            elem.color = PINK
                print(f"Updated {mat.name} color ramp to PINK")
            elif mat.name == "Material.071":
                # Orange/pink mix
                elems = list(node.color_ramp.elements)
                if len(elems) >= 2:
                    elems[0].color = ORANGE
                    elems[-1].color = PINK
                print(f"Updated {mat.name} color ramp to ORANGE->PINK")

# 4. Change one light to orange for variety
for obj in bpy.data.objects:
    if obj.type == 'LIGHT' and obj.name == "Area.001":
        obj.data.color = ORANGE[:3]
        print(f"Changed {obj.name} light to ORANGE")

print("="*60)

# Save if requested
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
