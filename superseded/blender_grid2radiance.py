# exports each selected object into its own file
import bpy
import os
import bmesh

def writeVtkPolydata(filename, verts, faces):
    #print verts[1]
    #print faces[1]
    vtkfile = open(filename, "w")
        
    #VTK legacy file header
    vtkfile.write("# vtk DataFile Version 2.0\n")
    vtkfile.write(filename+"\n")
    vtkfile.write("ASCII\n")
    vtkfile.write("DATASET POLYDATA\n")
    vtkfile.write("POINTS "+ str(len(verts)) + " float\n")

    #export points
    print("exporting points")
    for vert in verts:
        #print "exporting " + str(vert)
        line = ""
        for coord in vert.co:
            line +=  str(coord) + " "
        #vtkfile.write(str(vert.co[0]) + " " + str(vert.co[1]) + " "  + str(vert.co[2]) + "\n")
        vtkfile.write(line + "\n")
    #status message
    print("points exported")
                    
    #export polygons
    print("exporting polygons")
    total = 0
    fips = [(face, index) for index, face in enumerate(faces)] # face index polygons
    for fip in fips:
        #if len(face.v) > 2:
        total += (len(fip[0].vertices)+1)
    vtkfile.write("POLYGONS "+ str(len(fips)) + " " + str(total) + "\n")
    for fip in fips:
        #print "exporting " + str(face)
        num = len(fip[0].vertices)
        line = str(num) + " "
        #if len(face.v) > 2:
        for vertex in fip[0].vertices:
            line +=  str(vertex) + " "
        vtkfile.write(line + "\n")
    vtkfile.close()
   
   
# export to blend file location
basedir = os.path.dirname(bpy.data.filepath)

if not basedir:
    raise Exception("Blend file is not saved")

selection = bpy.context.selected_objects
bpy.ops.object.select_all(action='DESELECT')

for obj in selection:
    obj.select = True
    name = bpy.path.clean_name(obj.name)
    #print(name)
    if name[:len("Grid")] == "Grid" or name[:len("Grid")] == "grid":
        fn = os.path.join(basedir, name) # file name
        fnpnt = fn+".pnt"
        fnvtk = fn+".vtk"
        f = open(fnpnt,'w') # open file
        if obj.type=='MESH':
            od = obj.data # get object data if it is a mesh
            # export vertices and normals
            me = obj.to_mesh(bpy.context.scene, True, 'PREVIEW')
            #me = od
            me.transform(obj.matrix_world) # use world coordinates rather than local coordinate
            for v in me.vertices:
                x,y,z = v.co
                nx, ny, nz = v.normal
                print(x,y,z,nx,ny,nz)
                f.write('%s %s %s %s %s %s\n' % (x,y,z,nx,ny,nz))
            f.close()    
            #bpy.ops.export_scene.obj(filepath=fn + ".obj", use_selection=True, axis_forward='Y', axis_up='Z')
            ## Can be used for multiple formats
            # bpy.ops.export_scene.x3d(filepath=fn + ".x3d", use_selection=True)
            #obj.select = False
            print("grid file written:", fn)
            writeVtkPolydata(fnvtk,me.vertices,me.polygons)

for obj in selection:
    obj.select = True

