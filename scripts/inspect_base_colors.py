# Inspect ALL color sources including base colors, textures, etc.
import bpy

print("\n" + "="*60)
print("FULL COLOR INSPECTION")
print("="*60)

# Check Principled BSDF base colors
print("\n=== PRINCIPLED BSDF BASE COLORS ===")
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            base_color = node.inputs['Base Color'].default_value
            if base_color[0] > 0.01 or base_color[1] > 0.01 or base_color[2] > 0.01:
                print(f"{mat.name}:")
                print(f"  Base Color: ({base_color[0]:.2f}, {base_color[1]:.2f}, {base_color[2]:.2f})")

# Check for RGB nodes
print("\n=== RGB/COLOR NODES ===")
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'RGB':
            color = node.outputs[0].default_value
            print(f"{mat.name} - RGB node: ({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")

# Check compositing nodes
print("\n=== COMPOSITING NODES ===")
if bpy.context.scene.use_nodes and bpy.context.scene.node_tree:
    for node in bpy.context.scene.node_tree.nodes:
        print(f"  {node.type}: {node.name}")
        if hasattr(node, 'inputs'):
            for inp in node.inputs:
                if 'color' in inp.name.lower() or 'fac' in inp.name.lower():
                    if hasattr(inp, 'default_value'):
                        print(f"    {inp.name}: {inp.default_value}")

# Check for color ramps
print("\n=== COLOR RAMPS IN MATERIALS ===")
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'VALTORGB':  # Color Ramp
            print(f"{mat.name} - Color Ramp:")
            for i, elem in enumerate(node.color_ramp.elements):
                c = elem.color
                print(f"  Stop {i} at {elem.position:.2f}: ({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})")

# Check object colors (viewport display)
print("\n=== OBJECT DISPLAY COLORS ===")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        c = obj.color
        if c[0] != 1 or c[1] != 1 or c[2] != 1:
            print(f"{obj.name}: ({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})")

print("\n" + "="*60)
