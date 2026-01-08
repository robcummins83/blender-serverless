# Fix logo material to use alpha transparency
# Run: blender --background template.blend --python fix_logo_material.py -- --save

import bpy
import sys

print("\n" + "="*60)
print("FIXING LOGO MATERIAL FOR TRANSPARENCY")
print("="*60)

# Find the Logo_Material
mat = bpy.data.materials.get("Logo_Material")
if not mat:
    print("ERROR: Logo_Material not found!")
    sys.exit(1)

print(f"Found material: {mat.name}")

# Enable transparency
mat.blend_method = 'BLEND'  # or 'HASHED' for better performance
mat.shadow_method = 'HASHED'
mat.use_backface_culling = False

# Clear existing nodes and rebuild
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear all nodes
nodes.clear()

# Create nodes
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (400, 0)

emission = nodes.new('ShaderNodeEmission')
emission.location = (100, 100)
emission.inputs['Strength'].default_value = 5.0

tex_image = nodes.new('ShaderNodeTexImage')
tex_image.location = (-300, 100)

# Find the logo image
logo_img = None
for img in bpy.data.images:
    if 'logo' in img.name.lower() or 'temperature' in img.name.lower():
        logo_img = img
        break

if logo_img:
    tex_image.image = logo_img
    print(f"Using image: {logo_img.name}")
else:
    print("WARNING: Logo image not found in blend file!")

# Create transparent BSDF for mixing
transparent = nodes.new('ShaderNodeBsdfTransparent')
transparent.location = (100, -100)

# Mix shader based on alpha
mix = nodes.new('ShaderNodeMixShader')
mix.location = (250, 0)

# Connect nodes
# Image color -> Emission
links.new(tex_image.outputs['Color'], emission.inputs['Color'])

# Image alpha -> Mix factor
links.new(tex_image.outputs['Alpha'], mix.inputs['Fac'])

# Transparent -> Mix input 1 (where alpha is 0)
links.new(transparent.outputs['BSDF'], mix.inputs[1])

# Emission -> Mix input 2 (where alpha is 1)
links.new(emission.outputs['Emission'], mix.inputs[2])

# Mix -> Output
links.new(mix.outputs['Shader'], output.inputs['Surface'])

print("Material node tree rebuilt with alpha transparency")
print("="*60)

# Save if requested
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
