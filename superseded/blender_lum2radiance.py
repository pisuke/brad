# exports each selected object into its own file

import bpy
import os
import math

# export to blend file location
basedir = os.path.dirname(bpy.data.filepath)
lumname = bpy.path.display_name_from_filepath(bpy.data.filepath) +'.lum'
fn = os.path.join(basedir, lumname)
f = open(fn,'w')

if not basedir:
    raise Exception("Blend file is not saved")

selection = bpy.context.selected_objects

bpy.ops.object.select_all(action='DESELECT')

for obj in selection:

    obj.select = True
    
    
    if obj.type=='LAMP':
        #name = bpy.path.clean_name(obj.name)
        name = obj.name
        #print(obj.type)
        #print(name)
        #print(dir(obj.data))
        ies = obj.data.name
        #print(obj.location)
        x,y,z = obj.location
        #print(x,y,z)
        rx,ry,rz = obj.matrix_world.to_euler()
        #print(rx, ry, rz)
        rx = math.degrees(rx)
        ry = math.degrees(ry)
        rz = math.degrees(rz)
        #print(rx, ry, rz)
        #print(dir(obj.matrix_world))
        xform = '!xform -rx %s -ry %s -rz %s -t %s %s %s %s.ies # %s\n' % (rx, ry, rz, x, y, z, ies, name)
        print(xform)
        f.write(xform)
            

    obj.select = False

    

for obj in selection:
    obj.select = True

f.close()
print("written:", fn)