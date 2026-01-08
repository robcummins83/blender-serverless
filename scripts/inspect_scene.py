# Run this in Blender's Scripting tab to see all objects in the scene
import bpy

print("\n" + "="*50)
print("SCENE OBJECTS")
print("="*50)

for obj in bpy.data.objects:
    print(f"{obj.type:12} | {obj.name}")

print("\n" + "="*50)
print("TEXT OBJECTS")
print("="*50)

for obj in bpy.data.objects:
    if obj.type == 'FONT':
        text_data = obj.data
        print(f"Name: {obj.name}")
        print(f"Text: {text_data.body}")
        print(f"Location: {obj.location}")
        print("---")

print("\n" + "="*50)
print("MESH OBJECTS WITH 'AI' OR 'TEXT' IN NAME")
print("="*50)

for obj in bpy.data.objects:
    if 'ai' in obj.name.lower() or 'text' in obj.name.lower() or 'logo' in obj.name.lower():
        print(f"{obj.type:12} | {obj.name}")
