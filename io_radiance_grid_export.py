# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "Export Radiance Calculation Grids",
    "description": "Export Radiance Calculation Grids",
    "author": "Francesco Anselmo",
    "version": (0, 1),
    "blender": (2, 57, 0),
    "location": "File > Export > Export Radiance Calculation Grids (.pnt)",
    "warning": "",
    "wiki_url":"",
    "category": "Import-Export",
}



import bpy
import os
import bmesh
from mathutils import Vector
from os.path import splitext
from math import degrees

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

def write_grids(context, filepath, frame_start, frame_end, only_selected=False):

    data_attrs = (
        'lens',
        'shift_x',
        'shift_y',
        'dof_distance',
        'clip_start',
        'clip_end',
        'draw_size',
        )

    obj_attrs = (
        'hide_render',
        )
    
    fn = splitext(filepath)[0]

    scene = bpy.context.scene

    grids = []

    for obj in scene.objects:
        if only_selected and not obj.select:
            continue
        if obj.type != 'MESH':
            continue

        grids.append((obj, obj.data))

    frame_range = range(frame_start, frame_end + 1)


    for obj, obj_data in grids:
        gfn = '%s_%s' % (fn,obj.name)
        grid = obj
        name = obj.name

        if name[:len("Grid")] == "Grid" or name[:len("Grid")] == "grid":
            fn = gfn # file name
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
        
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper


class GridExporter(bpy.types.Operator, ExportHelper):
    """Export Radiance Calculation Grids"""
    
    bl_idname = "export.radiance_grids"

    bl_label = "Export Radiance Calculation Grids"

    filename_ext = ".pnt"
    filter_glob = StringProperty(default="*.pnt", options={'HIDDEN'})

    frame_start = IntProperty(name="Start Frame",
            description="Start frame for export",
            default=1, min=1, max=300000)
    frame_end = IntProperty(name="End Frame",
            description="End frame for export",
            default=1, min=1, max=300000)
    only_selected = BoolProperty(name="Only Selected",
            default=True)
            

    def execute(self, context):
        write_grids(context, self.filepath, self.frame_start, self.frame_start, self.only_selected)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end

        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_export(self, context):
    import os
    default_path = os.path.splitext(bpy.data.filepath)[0] + ".py"
    self.layout.operator(GridExporter.bl_idname, text="Radiance Calculation Grids (.pnt)").filepath = default_path


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()

