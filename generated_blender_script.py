import bpy
import math
import json
# from mathutils import Vector # Do not use this module

# 1. Parse JSON data and initialize scene
# Parse JSON string to Python dictionary
with open("F:/projects/sketch_to_blender/sketch.json", "r", encoding="utf-8") as f:
    json_string = f.read()
    data = json.loads(json_string)

# Scene settings
wall_height = 2.5
wall_thickness = 0.5
wall_objects = [] # List to store created wall objects

# Scene initialization
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 1. Wall Creation
for element in data['elements']:
    if element['type'] == 'wall':
        start = element['start']
        end = element['end']
        length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        center_3d = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, wall_height / 2)
        bpy.ops.mesh.primitive_cube_add(location=center_3d)
        wall = bpy.context.object
        wall.rotation_euler[2] = angle
        wall.dimensions = (length, wall_thickness, wall_height)
        wall_objects.append(wall)

# 2. Door/Window Creation
for element in data['elements']:
    if element['type'] == 'door' or element['type'] == 'window':
        position = element['position']
        door_size = (0.9, 2.1)
        window_size = (1.2, 1.2)
        hole_z_pos = 1.05 if element['type'] == 'door' else 1.5
        hole_dims = (door_size[0], wall_thickness * 2, door_size[1]) if element['type'] == 'door' else (window_size[0], wall_thickness * 2, window_size[1])
        hole_pos_2d = (position[0], position[1])

        min_dist = float('inf')
        closest_wall = None

        for wall in wall_objects:
            wall_pos_2d = (wall.location[0], wall.location[1])
            dist = math.sqrt((hole_pos_2d[0] - wall_pos_2d[0])**2 + (hole_pos_2d[1] - wall_pos_2d[1])**2)
            if dist < min_dist:
                min_dist = dist
                closest_wall = wall

        if closest_wall is not None:
            cutter_location_3d = (position[0], position[1], hole_z_pos)
            bpy.ops.mesh.primitive_cube_add(location=cutter_location_3d)
            cutter = bpy.context.object
            cutter.dimensions = hole_dims
            cutter.rotation_euler[2] = closest_wall.rotation_euler[2]

            bpy.context.view_layer.objects.active = closest_wall
            mod = closest_wall.modifiers.new(name="Hole", type='BOOLEAN')
            mod.object = cutter
            mod.operation = 'DIFFERENCE'
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cutter, do_unlink=True)