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
    "name": "Export Radiance Geometry",
    "description": "Export Radiance Geometry",
    "author": "Francesco Anselmo",
    "version": (0, 1),
    "blender": (2, 57, 0),
    "location": "File > Export > Export Radiance Geometry (.rad)",
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


def write_radiance(context, filepath, frame_start, frame_end, only_selected=False):

    fn = splitext(filepath)[0]

    scene = bpy.context.scene

    geometry = []

    for obj in scene.objects:
        if only_selected and not obj.select:
            continue
        if obj.type != 'MESH':
            continue

        geometry.append((obj, obj.data))
        obj.select = False

    frame_range = range(frame_start, frame_end + 1)

    for obj, obj_data in geometry:

        obj.select = True

        name = bpy.path.clean_name(obj.name)
        gfn = "%s_%s" % (fn, name)

        bpy.ops.export_scene.obj(filepath=gfn + ".obj", use_selection=True, axis_forward='Y', axis_up='Z')

        obj.select = False
        print("written: %s.obj" % gfn)
        
        os.system("obj2rad %s.obj > %s.rad" % (gfn,gfn))
        print("written: %s.rad" % gfn)

    for obj, obj_data in geometry:
        obj.select = True
        
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper


class RadianceExporter(bpy.types.Operator, ExportHelper):
    """Export Radiance Geometry"""
    
    bl_idname = "export.radiance_geometry"

    bl_label = "Export Radiance Geometry"

    filename_ext = ".rad"
    filter_glob = StringProperty(default="*.rad", options={'HIDDEN'})

    frame_start = IntProperty(name="Start Frame",
            description="Start frame for export",
            default=1, min=1, max=300000)
    frame_end = IntProperty(name="End Frame",
            description="End frame for export",
            default=1, min=1, max=300000)
    only_selected = BoolProperty(name="Only Selected",
            default=True)
            

    def execute(self, context):
        write_radiance(context, self.filepath, self.frame_start, self.frame_start, self.only_selected)
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
    self.layout.operator(RadianceExporter.bl_idname, text="Radiance Geometry (.rad)").filepath = default_path


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()

