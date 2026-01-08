# Comprehensive scene inspection - find all color sources
import bpy

print("\n" + "="*60)
print("COMPREHENSIVE COLOR INSPECTION")
print("="*60)

# 1. All materials with emission nodes
print("\n=== MATERIALS WITH EMISSION ===")
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            color = node.inputs['Color'].default_value
            strength = node.inputs['Strength'].default_value
            print(f"{mat.name}:")
            print(f"  Color: ({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")
            print(f"  Strength: {strength}")

# 2. All lights
print("\n=== LIGHTS ===")
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        light = obj.data
        color = light.color
        print(f"{obj.name} ({light.type}):")
        print(f"  Color: ({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")
        print(f"  Energy: {light.energy}")

# 3. World/environment
print("\n=== WORLD SETTINGS ===")
world = bpy.context.scene.world
if world and world.use_nodes:
    for node in world.node_tree.nodes:
        if node.type == 'BACKGROUND':
            color = node.inputs['Color'].default_value
            strength = node.inputs['Strength'].default_value
            print(f"Background Color: ({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")
            print(f"Background Strength: {strength}")

# 4. All materials - check for Principled BSDF emission
print("\n=== PRINCIPLED BSDF WITH EMISSION ===")
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            # Check emission inputs
            if 'Emission Color' in node.inputs:
                em_color = node.inputs['Emission Color'].default_value
                em_strength = node.inputs['Emission Strength'].default_value if 'Emission Strength' in node.inputs else 0
                if em_strength > 0:
                    print(f"{mat.name}:")
                    print(f"  Emission Color: ({em_color[0]:.2f}, {em_color[1]:.2f}, {em_color[2]:.2f})")
                    print(f"  Emission Strength: {em_strength}")

# 5. Objects with "ray" or "light" in name
print("\n=== OBJECTS WITH 'RAY' OR 'LIGHT' OR 'BEAM' IN NAME ===")
for obj in bpy.data.objects:
    name_lower = obj.name.lower()
    if 'ray' in name_lower or 'light' in name_lower or 'beam' in name_lower or 'glow' in name_lower or 'trail' in name_lower:
        print(f"{obj.type}: {obj.name}")
        if obj.type == 'MESH' and obj.data.materials:
            for mat in obj.data.materials:
                if mat:
                    print(f"  Material: {mat.name}")

# 6. All objects and their materials
print("\n=== ALL OBJECTS WITH MATERIALS ===")
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.materials:
        mats = [m.name for m in obj.data.materials if m]
        if mats:
            print(f"{obj.name}: {', '.join(mats)}")

print("\n" + "="*60)
