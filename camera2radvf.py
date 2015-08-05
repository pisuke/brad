# exports each selected object into its own file

import bpy
import os
from math import degrees
from mathutils import Matrix, Vector

# export to blend file location
basedir = os.path.dirname(bpy.data.filepath)

if not basedir:
    raise Exception("Blend file is not saved")

selection = bpy.context.selected_objects

bpy.ops.object.select_all(action='DESELECT')

# create list of static blender's data
def get_comp_data(context):
    scene = context.scene
    aspect_x = scene.render.pixel_aspect_x
    aspect_y = scene.render.pixel_aspect_y
    aspect = aspect_x / aspect_y
    start = scene.frame_start
    end = scene.frame_end
    fps = scene.render.fps

    return {
        'scn': scene,
        'width': scene.render.resolution_x,
        'height': scene.render.resolution_y,
        'aspect': aspect,
        'fps': fps,
        'start': start,
        'end': end,
        'duration': (end - start + 1.0) / fps,
        #'active_cam_frames': active_cam_frames,
        'curframe': scene.frame_current,
        }

data = get_comp_data(bpy.context)

def convert_transform_matrix(matrix, width, height, aspect, x_rot_correction=False):

    # get blender transform data for ob
    b_loc = matrix.to_translation()
    b_rot = matrix.to_euler('ZYX')  # ZYX euler matches AE's orientation and allows to use x_rot_correction
    b_scale = matrix.to_scale()

    x = (b_loc.x * 1.0) / aspect + width / 2.0  # calculate AE's X position
    y = (b_loc.y * 1.0) + (height / 2.0)  # calculate AE's Y position
    z = b_loc.z * 1.0  # calculate AE's Z position
    # Convert rotations to match AE's orientation.
    rx = degrees(b_rot.x)  # if not x_rot_correction - AE's X orientation = blender's X rotation if 'ZYX' euler.
    ry = -degrees(b_rot.y)  # AE's Y orientation is negative blender's Y rotation if 'ZYX' euler
    rz = -degrees(b_rot.z)  # AE's Z orientation is negative blender's Z rotation if 'ZYX' euler
    if x_rot_correction:
        rx -= 90.0  # In blender - ob of zero rotation lay on floor. In AE layer of zero orientation "stands"
    # Convert scale to AE scale
    sx = b_scale.x * 1.0  # scale of 1.0 is 100% in AE
    sy = b_scale.z * 1.0  # scale of 1.0 is 100% in AE
    sz = b_scale.y * 1.0  # scale of 1.0 is 100% in AE

    return x, y, z, rx, ry, rz, sx, sy, sz

for obj in selection:

    obj.select = True
    
    print(obj.type)
    
    if (obj.type == 'CAMERA'):
        print(dir(obj.data))
        #print(obj.location.x, obj.location.y, obj.location.z)
        print(dir(obj.rotation_euler))

        #print(dir(obj.rotation_axis_angle))
        #print(obj.delta_rotation_quaternion)
        name = bpy.path.clean_name(obj.name)
        fn = os.path.join(basedir, name)
        #x, y, z, rx, ry, rz, sx ,sy, sz = convert_transform_matrix(obj.matrix_world.copy(), data['width'], data['height'], data['aspect'], x_rot_correction=True)
        #print(transform)
        
        camera_view = (Vector([0,0,-1]) * obj.rotation_euler.to_matrix())
        #print(camera_view)
        
        vu = Vector((0.0, 1.0, 0.0))
        vuc  = vu * obj.matrix_world.to_3x3()
        
        vd = Vector((0.0, 0.0, -1.0))
        vdc  = vd * obj.matrix_world.to_3x3()
        
        print(vdc, vuc)
        
        print(fn)
        f = open(fn+'.vf','w')
        #f.write('rvu -vta -vp %s %s %s -vd %s %s %s')
        print("written:", fn+'.vf')
        f.close()

    obj.select = False

for obj in selection:
    obj.select = True