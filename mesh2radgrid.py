import os, time, bpy
import mathutils, bpy_extras.io_utils

print("export Radiance grid ...")

def name_compat(name):
    if name is None:
        return 'None'
    else:
        return name.replace(' ', '_')

def mesh2radgrid(filepath):
    basename, ext = os.path.splitext(filepath)
    name = bpy.path.clean_name(obj.name)
    fn = os.path.join(basename, name)
    context_name = [fn, '', '', '.pnt']  # Base name, scene name, frame number, extension
    scene = bpy.context.scene
    
    objects = bpy.context.selected_objects
    
    filepath = ''.join(context_name)
    
    def veckey3d(v):
        return round(v.x, 6), round(v.y, 6), round(v.z, 6)

    def veckey2d(v):
        return round(v[0], 6), round(v[1], 6)

    print(filepath)    
    file = open(filepath, "w", encoding="utf8", newline="\n")
    fw = file.write
    
    # Initialize totals, these are updated each object
    totverts = totuvco = totno = 1

    face_vert_index = 1

    globalNormals = {}
    
    copy_set = set()

    # Get all meshes
    for ob_main in objects:
        
        # ignore dupli children
        if ob_main.parent and ob_main.parent.dupli_type in {'VERTS', 'FACES'}:
            # XXX
            print(ob_main.name, 'is a dupli child - ignoring')
            continue

        obs = []
        if ob_main.dupli_type != 'NONE':
            # XXX
            print('creating dupli_list on', ob_main.name)
            ob_main.dupli_list_create(scene)

            obs = [(dob.object, dob.matrix) for dob in ob_main.dupli_list]

            # XXX debug print
            print(ob_main.name, 'has', len(obs), 'dupli children')
        else:
            obs = [(ob_main, ob_main.matrix_world)]

        for ob, ob_mat in obs:
            #print(ob, ob_mat)
            #print(dir(ob))
            mesh = ob.data
            #print(dir(mesh))
            for vert in mesh.vertices:
                #print(vert.co, vert.normal)
                #print(dir(vert))
                fw('%f %f %f %f %f %f\n' % (vert.co.x, vert.co.y, vert.co.z, vert.normal.x, vert.normal.y, vert.normal.z) )
        
        file.close()

mesh2radgrid(os.path.dirname(bpy.data.filepath))