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
    "name": "Export Radiance View Files",
    "description": "Export Radiance View Files",
    "author": "Francesco Anselmo francesco.anselmo@arup.com",
    "version": (0, 1),
    "blender": (2, 57, 0),
    "location": "File > Export > Export Radiance View Files (.vf)",
    "warning": "",
    "wiki_url":"",
    "category": "Import-Export",
}



import bpy
from mathutils import Vector
from os.path import splitext
from math import degrees

def write_cameras(context, filepath, frame_start, frame_end, only_selected=False):

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

    cameras = []

    for obj in scene.objects:
        if only_selected and not obj.select:
            continue
        if obj.type != 'CAMERA':
            continue

        cameras.append((obj, obj.data))

    frame_range = range(frame_start, frame_end + 1)


    for obj, obj_data in cameras:
        camfn = '%s_%s.vf' % (fn,obj.name)
        cam = obj
        vp = obj.location
        vu = cam.matrix_world.to_quaternion() * Vector((0.0, 1.0, 0.0))
        vd = cam.matrix_world.to_quaternion() * Vector((0.0, 0.0, -1.0))
        vpx, vpy, vpz = vp
        vux, vuy, vuz = vu
        vdx, vdy, vdz = vd
        lens = repr(getattr(obj_data, 'lens'))
        vh = degrees(float(repr(getattr(obj_data, 'angle_x'))))
        vv = degrees(float(repr(getattr(obj_data, 'angle_y'))))
        vs = float(repr(getattr(obj_data, 'shift_x')))
        vl = float(repr(getattr(obj_data, 'shift_y')))
        vo = float(repr(getattr(obj_data, 'clip_start')))
        va = float(repr(getattr(obj_data, 'clip_end')))
        if va>=1000000.0:
        	va = 0
        	vo = 0
        vtype = repr(getattr(obj_data, 'type')) # [‘PERSP’, ‘ORTHO’, ‘PANO’]
        vt = 'v'
        if vtype == 'ORTHO':
        	vt = 'l'
        if vtype == 'PANO':
        	vt = 'c'
        if vh>160.0 or vv>160.0:
        	vt = 'a'
        	vh = 180.0
        	vv = 180.0
        print(camfn, lens, vtype, vt, vp, vpx, vpy, vpz, vd, vdx, vdy, vdz, vu, vux, vuy, vuz, vh, vv, vo, va, vs, vl)
        fw = open(camfn, 'w').write
        fw('rvu -vt%s -vp %s %s %s -vd %s %s %s -vu %s %s %s -vh %s -vv %s -vo %s -va %s -vs %s -vl %s \n' % (vt, vpx, vpy, vpz, vdx, vdy, vdz, vux, vuy, vuz, vh, vv, vo, va, vs, vl))
        
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper


class CameraExporter(bpy.types.Operator, ExportHelper):
    """Export Blender Cameras to Radiance Views"""
    
    bl_idname = "export.radiance_views"

    bl_label = "Export Radiance View Files"

    filename_ext = ".vf"
    filter_glob = StringProperty(default="*.vf", options={'HIDDEN'})

    frame_start = IntProperty(name="Start Frame",
            description="Start frame for export",
            default=1, min=1, max=300000)
    frame_end = IntProperty(name="End Frame",
            description="End frame for export",
            default=1, min=1, max=300000)
    only_selected = BoolProperty(name="Only Selected",
            default=True)
            

    def execute(self, context):
        write_cameras(context, self.filepath, self.frame_start, self.frame_start, self.only_selected)
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
    self.layout.operator(CameraExporter.bl_idname, text="Radiance View Files (.vf)").filepath = default_path


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()

