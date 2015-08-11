bl_info = {
    "name":         "My Data Format",
    "author":       "Bruce Sutherland",
    "blender":      (2,6,2),
    "version":      (0,0,1),
    "location":     "File > Import-Export",
    "description":  "Export custom data format",
    "category":     "Import-Export"
}
        
import bpy
from bpy_extras.io_utils import ExportHelper

class ExportMyFormat(bpy.types.Operator, ExportHelper):
    bl_idname       = "export_my_format.fmt";
    bl_label        = "My Data Exporter";
    bl_options      = {'PRESET'};
    
    filename_ext    = ".fmt";
    
    def execute(self, context):
        return {'Finished'};

def menu_func(self, context):
    self.layout.operator(ExportMyFormat.bl_idname, text="My Model Format(.fmt)");

def register():
    bpy.utils.register_module(__name__);
    bpy.types.INFO_MT_file_export.append(menu_func);
    
def unregister():
    bpy.utils.unregister_module(__name__);
    bpy.types.INFO_MT_file_export.remove(menu_func);

if __name__ == "__main__":
    register()
