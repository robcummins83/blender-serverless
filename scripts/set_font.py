# Set Segoe UI Bold font for channel text and pack it
# Run: blender --background template.blend --python set_font.py -- --save

import bpy
import sys

print("\n" + "="*60)
print("SETTING FONT TO SEGOE UI BOLD")
print("="*60)

# Path to Segoe UI Bold on Windows
FONT_PATH = r"C:\Windows\Fonts\segoeuib.ttf"

# Load the font
try:
    font = bpy.data.fonts.load(FONT_PATH)
    print(f"Loaded font: {font.name}")
except Exception as e:
    print(f"ERROR loading font: {e}")
    sys.exit(1)

# Find the channel name text object
text_obj = bpy.data.objects.get("Channel_Name")
if not text_obj:
    print("ERROR: Channel_Name text object not found!")
    sys.exit(1)

# Apply the font
text_obj.data.font = font
print(f"Applied font to: {text_obj.name}")

# Pack the font into the .blend file so it works on RunPod
font.pack()
print("Font packed into .blend file")

print("="*60)

# Save if requested
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if "--save" in args:
        bpy.ops.wm.save_mainfile()
        print("FILE SAVED!")
