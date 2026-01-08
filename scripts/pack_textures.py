# Pack all external textures into the .blend file
# Run: blender --background template.blend --python pack_textures.py -- --save

import bpy
import sys

print("\n" + "="*60)
print("PACKING EXTERNAL TEXTURES")
print("="*60)

# List all images and their pack status
print("\nImages before packing:")
for img in bpy.data.images:
    packed = "PACKED" if img.packed_file else "EXTERNAL"
    filepath = img.filepath if img.filepath else "(no path)"
    print(f"  [{packed}] {img.name}: {filepath}")

# Pack all external images
packed_count = 0
for img in bpy.data.images:
    if not img.packed_file and img.filepath:
        try:
            img.pack()
            print(f"  PACKED: {img.name}")
            packed_count += 1
        except Exception as e:
            print(f"  FAILED to pack {img.name}: {e}")

print(f"\nPacked {packed_count} images")

# Also pack all external data (fonts, sounds, etc.)
print("\nPacking all external data...")
bpy.ops.file.pack_all()

print("\nImages after packing:")
for img in bpy.data.images:
    packed = "PACKED" if img.packed_file else "EXTERNAL"
    print(f"  [{packed}] {img.name}")

print("="*60)

# Check for --save argument
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
    else:
        print("Dry run - use --save to save changes")
else:
    print("Dry run - use --save to save changes")
