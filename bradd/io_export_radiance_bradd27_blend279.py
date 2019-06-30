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
    "name": "BRADD27 Export Radiance Files Directly",
    "description": "Export Radiance Files Directly",
    "author": "Francesco Anselmo francesco.anselmo@arup.com, Lucio Boscolo, dug9",
    "version": (27, 0),
    "blender": (2, 79, 0),
    "location": "File > Export > Export BRADD27 Radiance Folder (*)",
    "warning": "",
    "wiki_url":"https://github.com/pisuke/brad/tree/master/bradd/bradd_wiki/wiki_bradd27_blend279.html",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export",
}



import bpy
import os
import bmesh
from mathutils import Vector, Quaternion, Color, Matrix
from os.path import splitext
import math
from math import degrees

from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import ExportHelper


class RadianceExporter(bpy.types.Operator, ExportHelper):
    """Export to Radiance"""
    
    bl_idname = "export.radiance"

    bl_label = "BRADD Radiance Folder"

    filename_ext = "" #we want a folder name with no suffix if possible
    filter_glob = StringProperty(default="*.vf", options={'HIDDEN'})

    energy2lumensmantissa = FloatProperty(name="energy2lumens_mantissa",
            description="Lumens per unit of Lamp energy",
            default=.5, soft_min=-0.0, soft_max=1.0, step=1.0)
    energy2lumenspower = IntProperty(name="energy2lumens_power",
            description="mantissa x 10**power",
            default=0, soft_min=-3, soft_max=3, step=1)
    only_selected = BoolProperty(name="Only Selected",
            default=False)
    add_sky = BoolProperty(name="Add Sky",
            default=False)
            

    def execute(self, context):
        self.context = context
        self.folder = self.filepath
        self.camname = None
        self.images_to_convert = None
        self.make_folder()
        self.write_cameras()
        self.write_lighting()
        self.write_sky()
        self.write_radiance()
        self.copy_images()
        self.write_runs()
        self.write_rif()
        return {'FINISHED'}

    def invoke(self, context, event):
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end

        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    #3 options for holding export cross-function state:
    #1. instantiate a 2nd export class
    #2. call a wrapper export function to hold state between calls
    #3. add export functions to Exporter class
    # for fun / something different, here we implement #3
    def make_folder(self):
        os.mkdir(self.folder)
        return

    def is_visible(self,obj):
        # check if object is on a visible layer
        # when hacking a scene we often have construction junk on other layers
        vis = False
        for i in range(0,20):
            vis = vis or obj.layers[i] and bpy.context.scene.layers[i]
        return vis
        
    def write_cameras(self):

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
        
        fn = self.folder

        scene = bpy.context.scene

        cameras = []

        for obj in scene.objects:
            if self.only_selected and not obj.select:
                continue
            if not self.is_visible(obj):
                continue
            if obj.type != 'CAMERA':
                continue

            cameras.append((obj, obj.data))

        for obj, obj_data in cameras:
            cname = bpy.path.clean_name(obj.name)
            if self.camname is None:
                self.camname = cname
            camfn = os.path.join(fn,cname)+'.vf'
            cam = obj
            mtx = obj.matrix_world.copy()
            loc, rot, sca = mtx.decompose()
            #rot = rot.to_euler()
            vp = loc
            vu = rot * Vector((0.0, 1.0, 0.0))
            vd = rot * Vector((0.0, 0.0, -1.0))
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
            fw = open(camfn, 'w')
            if True:
                #leave out/zero -va aft clipping plane to see sky at infinity
                va = 0
                fw.write('rvu -vt%s -vp %s %s %s -vd %s %s %s -vu %s %s %s -vh %s -vv %s -vo %s -va %s -vs %s -vl %s \n' % (vt, vpx, vpy, vpz, vdx, vdy, vdz, vux, vuy, vuz, vh, vv, vo, va, vs, vl))
            else:
                #simpler default window shape, no clipping, and I can see the sky
                fw.write('rvu -vt%s -vp %s %s %s -vd %s %s %s -vu %s %s %s \n' % (vt, vpx, vpy, vpz, vdx, vdy, vdz, vux, vuy, vuz))
            fw.close()


    def make_sun(self):
        sun_str = """
void light solar
0
0
3 2.72e+06 2.72e+06 2.72e+06
        
solar source sun
0
0
4 -0.489041 -0.851114 0.190903 0.5

"""
        return sun_str

    def make_lamp(self, name, obj_data):
        """
        void light name.light
        0
        0
        3 37.99 37.99 37.99

        name.light sphere name
        0
        0
        4 0 0 0 .33
        """

        # 1. the energy / lumens / lamp part
        color = obj_data.color
        energy = obj_data.energy
        energy2lumens = self.energy2lumensmantissa
        energy2lumenspower =  self.energy2lumenspower
        ce = Vector((color[0],color[1],color[2])) * energy * energy2lumens * pow(10,energy2lumenspower)
        # enum in [‘POINT’, ‘SUN’, ‘SPOT’, ‘HEMI’, ‘AREA’], default ‘POINT’
        rad_type = 'light'
        n = 3
        lamp_type = obj_data.type
        if lamp_type == 'SPOT':
            rad_type = 'spotlight'
            n = 7
        str_light = 'void %s %s.light\n0\n0\n%d %f %f %f\n' % (rad_type,name,n,ce.x,ce.y,ce.z)
        if lamp_type == 'SPOT':
            # https://docs.blender.org/api/2.79/bpy.types.SpotLamp.html
            angle = degrees(obj_data.spot_size)
            (dx,dy,dz) = (0.0,0.0,-1.0)
            str_light = str_light + ' %f\n %f %f %f\n' % (angle,dx,dy,dz)

        # 2. the geometry part
        str_lamp = ''
        if lamp_type == 'POINT':
            # we will do a standard lightbulb sphere
            str_lamp = '%s.light sphere %s\n0\n0\n4 0 0 0 .33\n' % (name,name)
        elif lamp_type == 'SUN':
            # https://docs.blender.org/api/2.79/bpy.types.SunLamp.html
            str_lamp = self.make_sun()
            if obj_data.sky.use_sky:
                self.add_sky = True
        elif lamp_type == 'SPOT':
            # https://docs.blender.org/api/2.79/bpy.types.SpotLamp.html
            # we will do a lightbulb-radius disk/ring, offset from the cone tip
            radius = .33
            # sine = opposite / adjacent
            # adjacent = opposite / sine
            distance = radius / math.sin( obj_data.spot_size / 2.0 )
            str_lamp = '%s.light ring %s\n0\n0\n8 0 0 %f\n 0 0 -1\n 0 %f\n' % (name,name,-distance,radius)
        elif lamp_type == 'HEMI':
            # https://docs.blender.org/api/2.79/bpy.types.HemiLamp.html
            pass
        elif lamp_type == 'AREA':
            # https://docs.blender.org/api/2.79/bpy.types.AreaLamp.html
            dx = obj_data.size
            dy = dx
            if obj_data.shape == 'RECTANGLE':
                dy = obj_data.size_y
            str_lamp = '%s.light polygon %s\n0\n0\n12\n' % (name,name)
            str_lamp = str_lamp + ' %f %f 0.0\n' % (-dx,-dy)
            str_lamp = str_lamp + ' %f %f 0.0\n' % (-dx, dy)
            str_lamp = str_lamp + ' %f %f 0.0\n' % ( dx, dy)
            str_lamp = str_lamp + ' %f %f 0.0\n' % ( dx,-dy)
            
        return str_light + '\n' + str_lamp
        
    def write_lighting(self):
        # https://docs.blender.org/api/2.79/bpy.types.Lamp.html
        fn = self.folder

        scene = bpy.context.scene

        lighting = []

        for obj in scene.objects:
            if self.only_selected and not obj.select:
                continue
            if not self.is_visible(obj):
                continue
            if obj.type != 'LAMP':
                continue

            lighting.append((obj, obj.data))

        lumname = os.path.join(fn,'lights.lum')
        f = open(lumname,'w')


        for obj, obj_data in lighting:
        
            if obj.type=='LAMP':
                #name = bpy.path.clean_name(obj.name)
                name = obj.name
                #print(obj.type)
                #print(name)
                #print(dir(obj.data))

                ies = bpy.path.clean_name(obj_data.name)
                mtx = obj.matrix_world.copy()
                loc, rot, sca = mtx.decompose()
                (rx,ry,rz) = rot.to_euler()
                (x,y,z) = loc
                #print(rx, ry, rz)
                rx = degrees(rx)
                ry = degrees(ry)
                rz = degrees(rz)
                
                #print(rx, ry, rz)
                #print(dir(obj.matrix_world))
                xform = '!xform -rx %s -ry %s -rz %s -t %s %s %s %s.rad\n' % (rx, ry, rz, x, y, z, ies)
                print(xform)
                f.write(xform)
                str_lamp = self.make_lamp(ies,obj_data)
                fn3 = os.path.join(fn,ies);
                f2 = open(fn3+'.rad','w+')
                f2.write(str_lamp)
                f2.close()

            #obj.select = False

       
        f.close()
        print("written:", lumname)

    def make_sky_mat(self):
        sky_str = """
# Hemispherical Blue Sky
# Sunny with sun for Perth W.A
# on 16th March, 10:00 am
# !gensky 3 16 10 +s -a -32 -o 115.6 -m 120
void light solar
0
0
3 2.72e+06 2.72e+06 2.72e+06

solar source sun
0
0
4 -0.489041 -0.851114 0.190903 0.5

void brightfunc skyfunc
2 skybr skybright.cal
0
7 1 3.76e+00 3.72e+00 2.98e-01 -0.489041 -0.851114 0.190903

"""
        return sky_str

    def make_sky_rad(self):
        sky_str = """
skyfunc glow skyglow
0
0
4 .85 1.04 1.2 0

skyglow source sky
0
0
4 0 0 1 180

skyfunc glow groundglow
0
0
4 .8 1.1 .8 0

groundglow source ground
0
0
4 0 0 -1 180

"""
        return sky_str

    def write_sky(self):
        fn = self.folder
        if self.add_sky:
            sky_str = self.make_sky_mat()
            sfn = open(os.path.join(fn,"sky.mat"),"w+")
            sfn.write(sky_str)
            sfn.close()
            sky_str = self.make_sky_rad()
            sfn = open(os.path.join(fn,"sky.rad"),"w+")
            sfn.write(sky_str)
            sfn.close()
            
        return

    def make_material(self, mat, mat_name):
        """
        https://floyd.lbl.gov/radiance/refer/usman2.pdf 
        https://docs.blender.org/api/2.79/bpy.types.Material.html
        void plastic Material
        0
        0
        5 .7 .7 .7 0.05 0.005 #R G B Specularity Roughness
        """
        mat_type = "plastic"
        n = 5
        if Vector(mat.specular_color).length < 1.0:
            mat_type = "metal"
        if mat.raytrace_mirror.use:
            mat_type = "mirror"
            n = 3
        if mat.use_transparency:
            mat_type = "trans"
            n = 7
        if mat.emit > 0.0:
            mat_type = "glow"
            n = 4

        mat_str = "void %s %s\n" % (mat_type,mat_name)
        mat_str = mat_str + "0\n0\n"
        (r,g,b) = tuple(mat.diffuse_color * mat.diffuse_intensity)
        if mat_type == "mirror":
            (r,g,b) = tuple(mat.mirror_color * mat.raytrace_mirror.reflect_factor)
        if mat_type == "glow":
            (r,g,b) = mat.diffuse_color * mat.emit
        S = Vector(mat.specular_color).length * mat.specular_intensity * .2
        R = (1.0 - mat.specular_hardness/100.0) * 0.25
        mat_str = mat_str + "%d %f %f %f " % (n,r,g,b)
        if mat_type == "mirror":
            mat_str = mat_str + "\n"
        if mat_type == "plastic" or mat_type == "metal" or mat_type == "trans":
            mat_str = mat_str + "%f %f\n" % (S,R)
        if mat_type == "trans":
            rad_transparency = (1.0 - mat.alpha) * 2.0 #mystery factor vs docs:0 to 1
            rad_spec_trans = rad_transparency
            mat_str = mat_str + "%f %f\n" % (rad_transparency, rad_spec_trans)
        if mat_type == "glow":
            mat_str = mat_str + " %f\n" % (.5) #max radius?
        return mat_str

    def transform_from_xyz_uv(self, xyz_list, uv_list):
        # image textures in Blender have uv image coordinates for each mesh vertex
        # radiance uses a transform -scale, 3 translations, 3 rotations- 
        # to get from vertex to image texture space or vice versa
        # xyz_list - list of 3D vertices for a single face of a mesh
        # uv_list - list of 2D vertices for same face of a mesh
        # using Vector, Quaternion, Matrix from:
        # https://docs.blender.org/api/2.79/ Standalone Modules > Math Types

        scale = 1.0
        (rx,ry,rz) = (0.0,0.0,0.0)
        (tx,ty,tz) = (0.0,0.0,0.0)

        n = len(xyz_list)
        if len(uv_list) < n:
            print('ouch uv list different from xy list')
            n = len(uv_list)
        ninverse = 1.0/n
        #convert to mathutils.Vector format
        #https://docs.blender.org/api/2.79/mathutils.html#mathutils.Vector
        vertices = []
        uvs = []
        for i in range(0,n):
            vertices.append( Vector(xyz_list[i]) )
            uvs.append( Vector((uv_list[i][0],uv_list[i][1],0.0)) ) #uvs are now 3D

        if False:
            for i in range(0,n):
                print('xyz= %f %f %f ' % tuple(vertices[i].xyz))
                print('uvs= %f %f\n' % tuple(uvs[i].xy))
        # compute center of each
        pcenter = Vector([0,0,0])
        uvcenter = Vector([0,0,0])
        for i in range(0,n):
            pcenter = pcenter + vertices[i]
            uvcenter = uvcenter + uvs[i]
        pcenter = pcenter * ninverse
        uvcenter = uvcenter * ninverse
        # reduce to center
        for i in range(0,n):
            vertices[i] = vertices[i] - pcenter
            uvs[i] = uvs[i] - uvcenter
        quat_total = Quaternion((0,0,1),0)
        doing_rotation = True
        if doing_rotation:
            # compute face normals
            pnormal = Vector([0,0,0])
            uvnormal = Vector([0,0,0])
            for i in range(0,n):
                ii = (i+1) % n #next vertex in list
                vi = vertices[i].normalized()
                vii = vertices[ii].normalized()
                pnormal = pnormal + vi.cross(vii)
                uvsi = uvs[i].normalized()
                uvsii = uvs[ii].normalized()
                uvnormal = uvnormal + uvsi.cross(uvsii)
            pnormal = pnormal.normalized()
            uvnormal = uvnormal.normalized()
            print('pnormal='+str(pnormal))
            print('uvnormal='+str(uvnormal))
            # get the rotation between the 2 normals
            #cosine = uvnave.dot(pnave)
            #axis = uvnave.cross(pnave)
            #quat1 = uvnormal.rotation_difference(pnormal)
            quat1 = pnormal.rotation_difference(uvnormal)
            (axis,angle) = quat1.to_axis_angle()
            print('angle1 = '+str(degrees(angle))+' axis1='+str(axis))

            #quat = quaternion(axis,cosine)
            # rotate one into system of other
            for i in range(0,n):
                v1 = vertices[i].copy()
                vertices[i].rotate(quat1)
                v2 = vertices[i]
                print('b[%f %f %f] a[%f %f %f]' % (v1.x,v1.y,v1.z,v2.x,v2.y,v2.z))
            (axis,angle) = quat_total.to_axis_angle()
            print('quatT_='+str(quat_total.angle)+' '+str(quat_total.axis))
            print('quatT ='+str(angle)+' '+str(axis))
            quat_total = quat_total * quat1
            print('quat1='+str(quat1.angle)+' '+str(quat1.axis))
            print('quatT='+str(quat_total.angle)+' '+str(quat_total.axis))
            (axis,angle) = quat_total.to_axis_angle()
            print('quatT ='+str(angle)+' '+str(axis))
        # get the scale difference
        scale = 1.0
        doing_scale = True
        if doing_scale:
            scale = 0.0
            for i in range(0,n):
                scale = scale + uvs[i].length / vertices[i].length
            scale = scale * ninverse
            #scale one to the other
            for i in range(0,n):
                vertices[i] = vertices[i]*scale
        doing_rotation2 = False
        quat2 = Quaternion((0,0,1),0.0)
        if doing_rotation2:
            # find the rotation in the uv plane
            angle = 0.0
            axis = Vector((0,0,0))
            for i in range(0,n):
                #cosine = vertices[i].normalized().dot(uvs[i].normalized())
                #sine = vertices[i].normalized().cross(uvs[i].normalized()).length
                #angle = angle + math.atan2(sine,cosine)
                quatb = vertices[i].normalized().rotation_difference(uvs[i].normalized())
                angle = angle + quatb.angle
                axis = axis + quatb.axis
            angle = angle * ninverse
            axis = axis * ninverse
            print('angle2 = '+str(degrees(angle))+' axis2='+str(axis))
            #apply planar angle to one
            quat2 = Quaternion(uvnormal,angle)
            for i in range(0,n):
                vertices[i].rotate(quat2)
            quat_total = quat_total * quat2
        #done now they should align pretty close
        if True:
            for i in range(0,n):
                close = True
                close = close and math.isclose(vertices[i].x, uvs[i].x, abs_tol=.01)
                close = close and math.isclose(vertices[i].y, uvs[i].y, abs_tol=.01)
                close = close and math.isclose(vertices[i].z, 0.0, abs_tol=.01)
                if not close:
                    (x,y,z) = tuple(vertices[i].xyz)
                    (u,v) = tuple(uvs[i].xy)
                    print("Not close: %d [%f %f %f] [%f %f]" % (i,x,y,z,u,v) )
        # combine all the transforms into one
        M0 = Matrix.Translation(tuple((pcenter * -1.0).xyz))            
        M1 = Matrix.Rotation(quat1.angle,4,quat1.axis)
        M2 = Matrix.Scale(scale,4)
        M3 = Matrix.Rotation(quat2.angle,4,quat2.axis)
        M4 = Matrix.Translation(tuple(uvcenter.xyz))
        M = M4*M3*M2*M1*M0
        M.invert_safe()
        (trans,rot,scales) = M.decompose()
        (tx,ty,tz) = tuple(trans.xyz)
        (rx,ry,rz) = rot.to_euler()
        (rx,ry,rz) = (degrees(rx),degrees(ry),degrees(rz))
        scale = scales[0]    
        print('pcenter [%f %f %f] ' % tuple(pcenter.xyz))
        print('uvcenter [%f %f %f]' % tuple(uvcenter.xyz) )
        print('trans_total: [%f %f %f] ' % (tx,ty,tz))
        return (rx,ry,rz,scale,tx,ty,tz)

    def make_sphere(self,geom_name,radius,mat_name):
        geom_str = "%s sphere %s\n0\n0\n4 0 0 0 %f\n" % (mat_name,geom_name,radius)
        return geom_str
    
    def make_cylinder(self,geom_name,radius,depth,mat_name):
        geom_str = "%s cylinder %s\n0\n0\n7 0 0 %f 0 0 %f %f\n" % (mat_name,geom_name,-depth/2.0,depth/2.0,radius)
        return geom_str

    def make_cone(self,geom_name,radius1,radius2,depth,mat_name):
        geom_str = "%s cone %s\n0\n0\n8 0 0 %f 0 0 %f %f %f\n" % (mat_name,geom_name,-depth/2.0,depth/2.0,radius1,radius2)
        return geom_str

    def make_ring(self,geom_name,center,direction,radius1,radius2,mat_name):
        ring_str = "%s ring %s\n0\n0\n8 %f %f %f %f %f %f %f %f\n" % (mat_name,geom_name,center[0],center[1],center[2],direction[0],direction[1],direction[2],radius1,radius2)
        return ring_str
    def make_bbox(self,vertices):
        # make a bounding box from a list of vertices
        bbmin = [1e17,1e17,1e17]
        bbmax = [-1e17,-1e17,-1e17]
        for p in vertices:
            for i in range(0,len(p)):
                bbmin[i] = min(p[i],bbmin[i])
                bbmax[i] = max(p[i],bbmax[i])
        return (bbmin,bbmax)

    def mat_has_image(self,mat):
        image = None
        mat_name = mat.name
        if mat.active_texture:
            print('mat active_texture_index='+str(mat.active_texture_index))
            tex = mat.active_texture
            print('tex.type='+tex.type)
            if tex.type == 'IMAGE':
                print('image path='+tex.image.filepath)
                image = tex.image
        return image
    
    
    def make_mesh(self,obj_data,geom_name,mat,mat_name):
        # https://docs.blender.org/api/2.79/bpy.types.Mesh.html
        # https://docs.blender.org/api/2.79/bpy.types.Image.html
        print('texpace_size = '+str(obj_data.texspace_size))
        print('texpace_loc  = '+str(obj_data.texspace_location))
        print('texspace_size= %f %f %f' % (obj_data.texspace_size[0],obj_data.texspace_size[1],obj_data.texspace_size[2]))
        print('texspace_loc = %f %f %f' % (obj_data.texspace_location.x,obj_data.texspace_location.y,obj_data.texspace_location.z))
        print('use_uato_texspace= ' + str(obj_data.use_auto_texspace))
        print('num materials = '+ str(len(obj_data.materials)))
        # detect if there's an image texture
        image = self.mat_has_image(mat)

        vertices = []
        nv = len(obj_data.vertices)
        for i in range(0,nv):
            vertices.append(obj_data.vertices[i].co)
        #in case we need to make uvs from vertices for lazy method (see below)
        (bbmin,bbmax) = self.make_bbox(vertices)
        if image:
            (ix,iy) = image.size
            # https://floyd.lbl.gov/radiance/refer/usman2.pdf
            # p.30:
            # The dimensions of the image are normalised so that the smaller dimension
            # is always one unit in length with the other dimension being
            # the ratio between the larger and the smaller.
            # ie An image of 5ØØ x 388 would have the box coordinate size of ( Ø, Ø ) to ( 1.48, 1 ).            
            uvblend2uvrad_scales = [ix/iy,1.0]
            if iy > ix:
                uvblend2uvrad_scales = [1.0,iy/ix]
            #look for uvs
            uv_layer = None
            # https://docs.blender.org/api/2.79/bpy.types.MaterialTextureSlot.html#bpy.types.MaterialTextureSlot
            # if not UV, assume GENERATED
            if mat.texture_slots[0].texture_coords == 'UV':
                if obj_data.uv_layers.active:
                    uv_layer = obj_data.uv_layers.active.data
            image_path_rel = image.filepath
            if image_path_rel[0:2] == '//':
                image_path_rel = image.filepath[2:]
            blend_path = os.path.dirname(bpy.data.filepath)
            image_path_abs = os.path.join(blend_path,image_path_rel)
            image_path_base = os.path.basename(image_path_rel)
            (image_path_root,image_path_ext) = os.path.splitext(image_path_base)
            image_path_ext = image_path_ext[1:] #get rid of the .
            image_path_scene = 'images/%s.hdr' % image_path_root
            # later, write out a .bat / .sh to convert images to .hdr and move to scene/images folder
            if self.images_to_convert is None:
                self.images_to_convert = {} 
            self.images_to_convert[image_path_root] = (image_path_abs,image_path_ext,image) #dict will elliminate duplicates
                
        geom_str = ""
        pcount = 0
        for poly in obj_data.polygons:
            modifier = mat_name
            texture_name = None
            tex_str = ""
            if image:
                """
                Material colorpict Material_pict
                13 clip_r clip_g clip_b images/test_image.hdr picture.cal pic_u pic_v  -t -.8 -.5 0.0 -s 1.25
                0
                0
                """
                texture_name = '%s.p%s_pict' % (geom_name,str(pcount))
                modifier = texture_name
                tex_str = "%s colorpict %s\n" % (mat_name,texture_name)
            poly_str = "%s polygon %s.p%s\n0\n0\n" % (modifier,geom_name,str(pcount))
            poly_str = poly_str + "%d\n" % (poly.loop_total * 3)
            uv_list = []
            xyz_list = []
            for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                vertex_index = obj_data.loops[loop_index].vertex_index
                poly_str = poly_str + "  %.6f %.6f %.6f\n" % tuple(vertices[vertex_index])
                if image:
                    xyz_list.append(vertices[vertex_index])
                    if uv_layer:
                        # uv layer is detailed way,
                        # in blender, Materials > Mapping > change GENERATED to UV
                        # and Edit Mode, Mesh > uv unwrap > uv unwrap or smart uv unwrap
                        # highlight a mesh face, and switch to UV Editor to correct
                        uv = uv_layer[loop_index].uv
                        uv_list.append([uv[0],uv[1]])
                    else:
                        # no uv_layer is the 'lazy way',
                        # in blender just add a texture, type=IMAGE or MOVIE, and Image > Open
                        # Materials > Mapping leave default GENERATED (which is GLOBAL, although here we assume OBJECT)
                        # then mesh vertices xy are scaled and translated to 0 - 1 range and used as uvs
                        # OK for Plane geometry
                        v = vertices[vertex_index]
                        uv = [0,0]
                        #scale object xy to 0 to 1 blender UV range
                        uv[0] = (v[0]-bbmin[0])/(bbmax[0]-bbmin[0]) 
                        uv[1] = (v[1]-bbmin[1])/(bbmax[1]-bbmin[1])
                        uv_list.append(uv)
            if image:
                print('before uv scaling')
                for i in range(0,len(uv_list)):
                    print('[%f %f %f] [%f %f]' % (xyz_list[i][0],xyz_list[i][1],xyz_list[i][2],uv_list[i][0],uv_list[i][1]))
                print('after uv scaling')
                for i in range(0,len(uv_list)):
                    # rescale UVs from blender 0 to 1 range
                    # into Radiance aspect ratio range (0 - 1 on short axis, 0 to 1+ on long axis)
                    uv_list[i][0] = uv_list[i][0] * uvblend2uvrad_scales[0]
                    uv_list[i][1] = uv_list[i][1] * uvblend2uvrad_scales[1]
                    print('[%f %f %f] [%f %f]' % (xyz_list[i][0],xyz_list[i][1],xyz_list[i][2],uv_list[i][0],uv_list[i][1]))
                # blender solves internally for a texture coordinate based  on XYZ, UV coords
                # goiong triangle by triangle, can do barycentric to barycentric, but for full polygon
                # I think it would be an 11 parameter, 2-point perspective transform
                # - 3 scales, 3 rotations, 3 translations, and 2 perspectives, or
                # radiance uses a 3D similarity transform (single an-isotropic scale, 3 rotations, 3 translations)
                #- only 7 parameter transform, so can't do complete job
                # here we attempt to compute the closest radiance similarity transform to replace XYZ,UV mapping:
                (rx,ry,rz,scale,tx,ty,tz) = self.transform_from_xyz_uv(xyz_list,uv_list)
                # https://docs.blender.org/api/2.79/bpy.types.Image.html
                ns = 19
                tex_str = tex_str + "%d clip_r clip_g clip_b %s picture.cal " % (ns,image_path_scene)
                tex_str = tex_str + "pic_u pic_v "
                tex_str = tex_str + "-rx %f -ry %f -rz %f " % (rx,ry,rz)
                tex_str = tex_str + "-s %f " % (scale)
                tex_str = tex_str + "-t %f %f %f " % (tx,ty,tz)
                tex_str = tex_str + "\n0\n0\n\n"
                    
            pcount = pcount + 1
            geom_str = geom_str + tex_str + poly_str + '\n'
        return geom_str

    def make_grid(self,obj_data,geom_name,mat,mat_name):
        #Quad faces are non-planar, so need to be split into 2 triangles

        # detect if there's an image texture
        image = self.mat_has_image(mat)

        vertices = []
        nv = len(obj_data.vertices)
        for i in range(0,nv):
            vertices.append(obj_data.vertices[i].co)
        #in case we need to make uvs from vertices for lazy method (see below)
        (bbmin,bbmax) = self.make_bbox(vertices)
        if image:
            (ix,iy) = image.size
            # https://floyd.lbl.gov/radiance/refer/usman2.pdf
            # p.30:
            # The dimensions of the image are normalised so that the smaller dimension
            # is always one unit in length with the other dimension being
            # the ratio between the larger and the smaller.
            # ie An image of 5ØØ x 388 would have the box coordinate size of ( Ø, Ø ) to ( 1.48, 1 ).            
            uvblend2uvrad_scales = [ix/iy,1.0]
            if iy > ix:
                uvblend2uvrad_scales = [1.0,iy/ix]
            #look for uvs
            uv_layer = None
            # https://docs.blender.org/api/2.79/bpy.types.MaterialTextureSlot.html#bpy.types.MaterialTextureSlot
            # if not UV, assume GENERATED
            if mat.texture_slots[0].texture_coords == 'UV':
                if obj_data.uv_layers.active:
                    uv_layer = obj_data.uv_layers.active.data
            image_path_rel = image.filepath
            if image_path_rel[0:2] == '//':
                image_path_rel = image.filepath[2:]
            blend_path = os.path.dirname(bpy.data.filepath)
            image_path_abs = os.path.join(blend_path,image_path_rel)
            image_path_base = os.path.basename(image_path_rel)
            (image_path_root,image_path_ext) = os.path.splitext(image_path_base)
            image_path_ext = image_path_ext[1:] #get rid of the .
            image_path_scene = 'images/%s.hdr' % image_path_root
            # later, write out a .bat / .sh to convert images to .hdr and move to scene/images folder
            if self.images_to_convert is None:
                self.images_to_convert = {} 
            self.images_to_convert[image_path_root] = (image_path_abs,image_path_ext,image) #dict will elliminate duplicates

        geom_str = ""
        pcount = 0
        for poly in obj_data.polygons:
            verts = []
            for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                vertex_index = obj_data.loops[loop_index].vertex_index
                verts.append(obj_data.vertices[vertex_index].co)
            # IDEA: split quad into triangles along the biggest height difference if there is one
            ii = 0
            if math.fabs(verts[0][2] - verts[2][2]) < math.fabs(verts[1][2] - verts[3][2]):
                ii = 1
            for itri in range(0,2):
                modifier = mat_name
                texture_name = None
                tex_str = ""
                if image:
                    """
                    Material colorpict Material_pict
                    13 clip_r clip_g clip_b images/test_image.hdr picture.cal pic_u pic_v  -t -.8 -.5 0.0 -s 1.25
                    0
                    0
                    """
                    texture_name = '%s.p%s_pict' % (geom_name,str(pcount))
                    modifier = texture_name
                    tex_str = "%s colorpict %s\n" % (mat_name,texture_name)
                
                poly_str = "%s polygon %s.p%s\n0\n0\n" % (modifier,geom_name,str(pcount))
                poly_str = poly_str + "%d\n" % (3 * 3)
                uv_list = []
                xyz_list = []
                iv0 = itri *2   #(0 or 2) for first vertex
                iv1 = iv0 + 1   #(1 or 3) for 2nd vertex
                iv2 = (iv1 + 1 + ii) % 4  # (2 or 0), or (3 or 1) for 3rd vertex depending on which way we split
                #print('iv0,iv1,iv2='+str(iv0)+' '+str(iv1)+' '+str(iv2)+' ii='+str(ii))
                iv = [iv0, iv1, iv2]
                for ip in range(0,3):
                    vert = verts[iv[ip]]
                    poly_str = poly_str + "  %.6f %.6f %.6f\n" % (vert[0],vert[1],vert[2])

                    if image:
                        xyz_list.append([vert[0],vert[1],0.0])
                        if uv_layer:
                            # uv layer is detailed way,
                            # in blender, Materials > Mapping > change GENERATED to UV
                            # and Edit Mode, Mesh > uv unwrap > uv unwrap or smart uv unwrap
                            # highlight a mesh face, and switch to UV Editor to correct
                            uv = uv_layer[loop_index].uv
                            uv_list.append([uv[0],uv[1]])
                        else:
                            # no uv_layer is the 'lazy way',
                            # in blender just add a texture, type=IMAGE or MOVIE, and Image > Open
                            # Materials > Mapping leave default GENERATED (which is GLOBAL, although here we assume OBJECT)
                            # then mesh vertices xy are scaled and translated to 0 - 1 range and used as uvs
                            # OK for Plane geometry
                            v = xyz_list[ip]
                            uv = [0,0]
                            #scale object xy to 0 to 1 blender UV range
                            uv[0] = (v[0]-bbmin[0])/(bbmax[0]-bbmin[0]) 
                            uv[1] = (v[1]-bbmin[1])/(bbmax[1]-bbmin[1])
                            uv_list.append(uv)
                if image:
                    print('before uv scaling')
                    for i in range(0,len(uv_list)):
                        print('[%f %f %f] [%f %f]' % (xyz_list[i][0],xyz_list[i][1],xyz_list[i][2],uv_list[i][0],uv_list[i][1]))
                    print('after uv scaling')
                    for i in range(0,len(uv_list)):
                        # rescale UVs from blender 0 to 1 range
                        # into Radiance aspect ratio range (0 - 1 on short axis, 0 to 1+ on long axis)
                        uv_list[i][0] = uv_list[i][0] * uvblend2uvrad_scales[0]
                        uv_list[i][1] = uv_list[i][1] * uvblend2uvrad_scales[1]
                        print('[%f %f %f] [%f %f]' % (xyz_list[i][0],xyz_list[i][1],xyz_list[i][2],uv_list[i][0],uv_list[i][1]))
                    # blender solves internally for a texture coordinate based  on XYZ, UV coords
                    # goiong triangle by triangle, can do barycentric to barycentric, but for full polygon
                    # I think it would be an 11 parameter, 2-point perspective transform
                    # - 3 scales, 3 rotations, 3 translations, and 2 perspectives, or
                    # radiance uses a 3D similarity transform (single an-isotropic scale, 3 rotations, 3 translations)
                    #- only 7 parameter transform, so can't do complete job
                    # here we attempt to compute the closest radiance similarity transform to replace XYZ,UV mapping:
                    (rx,ry,rz,scale,tx,ty,tz) = self.transform_from_xyz_uv(xyz_list,uv_list)
                    # https://docs.blender.org/api/2.79/bpy.types.Image.html
                    ns = 19
                    tex_str = tex_str + "%d clip_r clip_g clip_b %s picture.cal " % (ns,image_path_scene)
                    tex_str = tex_str + "pic_u pic_v "
                    tex_str = tex_str + "-rx %f -ry %f -rz %f " % (rx,ry,rz)
                    tex_str = tex_str + "-s %f " % (scale)
                    tex_str = tex_str + "-t %f %f %f " % (tx,ty,tz)
                    tex_str = tex_str + "\n0\n0\n\n"
                pcount = pcount + 1
                geom_str = geom_str + tex_str + poly_str + '\n'
                
        return geom_str

    def make_text(self,obj_data,geom_name,mat_name):
        # https://docs.blender.org/api/2.79/
        # https://docs.blender.org/api/2.79/bpy.types.Text.html
        # https://docs.blender.org/api/2.79/bpy.types.TextCurve.html
        # blender: text is geometry/textcurves,
        #    0,0 at lower-left of first line
        # radiance: text is a texture/modifier to be applied to geometry
        #    0,0 is upper-left of first text row
        # solution: create a plane / polygon the size of the paragraph
        #  use radiance mixtext modifier with 4 <Material> void <font.fnt> <Text.txt>
        #  and shift -ysize
        #  put Material name, and mixtext in Text.rad
        #  xform - do not use -m <material>
        fn = self.folder
        txt_name_clean = bpy.path.clean_name(geom_name)
        txt_rep_name = os.path.join(fn,"geom",txt_name_clean + '.txt' )
        gfn =  open(txt_rep_name,"w+")
        gfn.write(obj_data.body)
        gfn.close()
        """
        void mixtext Text_mat
        4 Material void helvet.fnt Text.txt
        0
        9 0 0 0 .25 0 0  0.5 0 0
        """
        ysize = obj_data.size
        xsize = ysize * .5
        shear = obj_data.shear * ysize
        lines = obj_data.body.split('\n')
        nlines = len(lines)
        longest = 0
        for i in range(0,nlines):
            longest = max(longest,len(lines[i]))
        sx = longest * xsize + shear
        sy = nlines * ysize 
        text_str = "void mixtext %s_mat\n" % (txt_name_clean)
        text_str = text_str + "4 %s void helvet.fnt geom/%s.txt\n" % (mat_name,txt_name_clean)
        text_str = text_str + "0\n9\n"
        text_str = text_str + "%f %f %f \n" % (shear,ysize,0.0)  # position
        text_str = text_str + "%f %f %f \n" % (xsize,0.0,0.0)  # row vector
        text_str = text_str + "%f %f %f \n\n" % (-shear,-ysize,0.0) # column vector
        
        text_str = text_str + "%s_mat polygon %s\n0\n0\n12\n" % (txt_name_clean,txt_name_clean)
        text_str = text_str + " %f %f 0.0\n" % (0.0,ysize)
        text_str = text_str + " %f %f 0.0\n" % (0.0,-sy + ysize)
        text_str = text_str + " %f %f 0.0\n" % (sx,-sy + ysize)
        text_str = text_str + " %f %f 0.0\n" % (sx,ysize)
        return text_str

    
    def make_geometry(self, obj_data, geom_name, mat, mat_name):
        """
        1) for sphere and icosphere, cylinder, cone, including endcap permutations and depth/radius permutations
        goal: export as radiance analytical surfaces if possible
        -relies on scene author to:
            a) NOT edit > 'apply' rotation or translation to geometry
                - can apply xy isotropic scale and any z scale
                - if scale isotropic, can leave in obj
            b( NOT do an-isotropic scale in the Object (or general in the transform stack)
                - if you have an an-isotropic scale, then apply it and do rule c) about renaming geometry
            c) if edit / hack the geometry, then change the geometry name
                from Sphere.001 etc to zphere.001 kone.001 sylinder.001
                or other non-keyword sphere,cylinder,cone containing names
                (obj name can contain those keywords)
                this renaming will cause it to export as general mesh
        for general mesh: export as polgyons
        """
        geom_str = ""
        raw_name = obj_data.name.lower()
        if 'sphere' in raw_name:
            vertices = obj_data.vertices
            faces = obj_data.polygons
            # icosphere first vertex z is radius
            # sphere first vertex 0,y,z is at radius, but need distance via root
            radius = math.sqrt(vertices[0].co[1]*vertices[0].co[1] + vertices[0].co[2]*vertices[0].co[2])
            geom_str = self.make_sphere(geom_name,radius,mat_name)
        elif 'cylinder' in raw_name:
            vertices = obj_data.vertices
            faces = obj_data.polygons
            lastface = len(faces) -1
            #blender has 3 options for end-caps
            # a) none / nocaps b) triangle fan (with point in middle of cap) c) ngon - whole end is one big polygon
            fan = faces[0].loop_total == 3
            ngon = faces[lastface].loop_total > 4  #ngon puts its big endcap faces at the end 
            nocap = not fan and not ngon
            ifirst = 0
            # fan puts the end-cap middle points first in vertex list
            if fan:
                ifirst = 2
            radius = vertices[ifirst].co[1]
            depth = -2.0 * vertices[ifirst].co[2]
            geom_str = self.make_cylinder(geom_name,radius,depth,mat_name)
            if not nocap:
                center = [0.0,0.0,-depth/2.0]
                direction = [0.0,0.0,-1.0]
                geom_str = geom_str + self.make_ring(geom_name+"_cap1",center,direction,radius,0.0,mat_name)
                center = [0.0,0.0,depth/2.0]
                direction = [0.0,0.0,1.0]
                geom_str = geom_str + self.make_ring(geom_name+"_cap2",center,direction,radius,0.0,mat_name)
                
        elif 'cone' in raw_name:
            vertices = obj_data.vertices
            faces = obj_data.polygons
            lastface = len(faces) -1
            # cone cap options are same as cylinder: nocap, fan, ngon
            fan = math.isclose(vertices[0].co[1], 0.0, rel_tol=1e-5)
            ngon = faces[lastface].loop_total > 4
            nocap = not fan and not ngon
            # a cone can end at a point or at a second face or slice or section
            # if it ends at a point, the sides will be triangles
            # if it ends at a section, sides will be quads
            section = (fan or nocap) and faces[lastface].loop_total == 4
            section = section or ngon and faces[0].loop_total == 4
            ifirst = 0
            if fan:
                ifirst = 1
                if section:
                    ifirst = 2
            radius1 = vertices[ifirst].co[1]
            depth = -2.0 * vertices[ifirst].co[2]
            radius2 = 0.0
            if section:
                isecond = 1
                if fan:
                    isecond = 3 #fan puts both its endcap middle points first
                radius2 = vertices[isecond].co[1]
            geom_str = self.make_cone(geom_name,radius1,radius2,depth,mat_name)
            if not nocap:
                center = [0.0,0.0,-depth/2.0]
                direction = [0.0,0.0,-1.0]
                geom_str = geom_str + self.make_ring(geom_name+"_cap1",center,direction,radius1,0.0,mat_name)
                if section:
                    center = [0.0,0.0,depth/2.0]
                    direction = [0.0,0.0,1.0]
                    geom_str = geom_str + self.make_ring(geom_name+"_cap2",center,direction,radius2,0.0,mat_name)
            
        elif 'grid' in raw_name:
            geom_str = self.make_grid(obj_data,geom_name,mat,mat_name)
        elif 'text' in raw_name:
            geom_str = self.make_text(obj_data,geom_name,mat_name)
        else:
            geom_str = self.make_mesh(obj_data,geom_name,mat,mat_name)
        return geom_str

        
    def write_radiance(self):
        """
        Goal: 2-tier system
        1. each geometry in a spearate .rad file
        2. one scene.rad that xforms the geometry into place, with material name
        """
        fn = self.folder

        scene = bpy.context.scene

        objs = []
        geoms = []
        texts = []
        materials = []

        for obj in scene.objects:
            if self.only_selected and not obj.select:
                continue
            if not self.is_visible(obj):
                continue
            if obj.type != 'MESH' and obj.type != 'FONT':
                continue
            geom_name = obj.data.name
            if obj.active_material is None:
                mat_name = "void"
            else:
                mat_name = obj.active_material.name
                materials.append(mat_name)
            objs.append((obj, geom_name,mat_name))
            geoms.append((geom_name,obj.type,mat_name))

        # MATERIALS
        #remove duplicates from materials
        materials = list(dict.fromkeys(materials).keys())
        mat_rep_name = os.path.join(fn,'materials.mat')
        mfn = open(mat_rep_name,"w+")
        for mat_name in materials:
            mat = bpy.data.materials[mat_name]
            mat_str = self.make_material(mat,mat_name)
            mfn.write(mat_str)
        mfn.close()
        
        # GEOMS
        #remove duplicates from geoms (obj_data)
        geoms = list(dict.fromkeys(geoms).keys())
        os.mkdir(os.path.join(fn,"geom"))
        for (geom_name,obj_type,mat_name) in geoms:
            mat = bpy.data.materials[mat_name]
            if obj_type == 'MESH':
                obj_data = bpy.data.meshes[geom_name]
            elif obj_type == 'FONT':
                obj_data = bpy.data.curves[geom_name]
            geom_str = self.make_geometry(obj_data,geom_name,mat,mat_name)
            geom_name_clean = bpy.path.clean_name(geom_name)
            geom_rep_name = os.path.join(fn,"geom",geom_name_clean + '.rad')
            gfn =  open(geom_rep_name,"w+")
            gfn.write(geom_str)
            gfn.close()

        # OBJECTS
        scene_rep_name = os.path.join(fn,'scene.rad')
        sfn = open(scene_rep_name,"w+")
        for obj, geom_name, mat_name in objs:
            mat = bpy.data.materials[mat_name]
            geom_name_clean = "geom/" + bpy.path.clean_name(geom_name)
            pre_name = obj.name + '_'
            mtx = obj.matrix_world.copy()
            loc, rot, sca = mtx.decompose()
            (rx,ry,rz) = rot.to_euler()
            (x,y,z) = loc
            
            #print(rx, ry, rz)
            rx = degrees(rx)
            ry = degrees(ry)
            rz = degrees(rz)
            (sx,sy,sz) = sca
            sx1 = math.isclose(sx, 1.0, rel_tol=1e-5)
            sy1 = math.isclose(sy, 1.0, rel_tol=1e-5)
            sz1 = math.isclose(sz, 1.0, rel_tol=1e-5)
            xform = '!xform -n %s ' % (pre_name)
            have_scale = not sx1 or not sy1 or not sz1
            if have_scale:
                have_isotropic = math.isclose(sx,sy, rel_tol=1e-5) and math.isclose(sx,sz, rel_tol=1e-5)
                if not have_isotropic:
                    # an-isotropic scales don't make sense/hard to do for analytical surfaces ie sphere
                    print('ouch - an-isotropic scale not handled by xform, using SX\n')
                xform = xform + '-s %s ' % (sx)
            xform = xform + '-rx %s -ry %s -rz %s -t %s %s %s %s.rad\n' % (rx, ry, rz, x, y, z, geom_name_clean)
            sfn.write(xform)
        sfn.close()

        return

    def write_picture_cal(self):
        # my windows system rvu can't find picture.cal
        # so we'll write it out.
        str_picture_cal = """
{
	Calculation of 2d picture coordinates.
	Picture is projected onto xy plane with lower left corner at origin.

	A1		- Ratio of height to width for tiles.
	A2		- Average red value for fadered or grey for fadegrey
	A3		- Average green value for fadegreen
	A4		- Average blue value for fadeblue
}
					{ straight coordinates }
pic_u = Px;
pic_v = Py;
					{ compute borders for mixfunc }
inpic = if(and(pic_u, and(pic_v,
		if(pic_aspect-1, and(1-pic_u,pic_aspect-pic_v),
				and(1/pic_aspect-pic_u,1-pic_v) ) ) ), 1, 0);
					{ standard tiling }
tile_u = mod(pic_u,max(1,1/pic_aspect));
tile_v = mod(pic_v,max(1,pic_aspect));
					{ tiling with inversion matching }
match_u = tri(pic_u,max(1,1/pic_aspect));
match_v = tri(pic_v,max(1,pic_aspect));
					{ brick-type staggering }
stag_u = if(pic_aspect-1,
		frac(if(frac(pic_v/pic_aspect/2)-.5,pic_u,pic_u+.5)),
		mod(if(frac(pic_v/2)-.5,pic_u,pic_u+.5/pic_aspect),
			1/pic_aspect));
stag_v = tile_v;

pic_aspect = if(arg(0)-.5, arg(1), 1);
					{ fade colors for distant viewing }
fadered(r,g,b) = fade(r, A2, T*.1);
fadegreen(r,g,b) = fade(g, A3, T*.1);
fadeblue(r,g,b) = fade(b, A4, T*.1);
fadegrey(r,g,b) = fade(grey(r,g,b), A2, T*.1);
"""

        fn = self.folder
        rfn = open(os.path.join(fn,"picture.cal"),"w+")
        rfn.write(str_picture_cal)
        rfn.close()
        
        
    def copy_images(self):
        # if we have image textures, radiance takes .hdr format
        # this method goes over the image textures used, and
        # saves them in HDR format using blender settings
        #
        ##https://docs.blender.org/api/2.79/bpy.types.ImageFormatSettings.html
        ###bpy.types.ImageFormatSettings 
        ##.file_format (to save to)
        ##enum in [‘BMP’, ‘IRIS’, ‘PNG’, ‘JPEG’, ‘JPEG2000’, ‘TARGA’, ‘TARGA_RAW’, ‘CINEON’, ‘DPX’, ‘OPEN_EXR_MULTILAYER’, ‘OPEN_EXR’, ‘HDR’, ‘TIFF’, ‘AVI_JPEG’, ‘AVI_RAW’, ‘FRAMESERVER’, ‘FFMPEG’], default ‘TARGA’
        ##.color_mode 
        ##enum in [‘BW’, ‘RGB’, ‘RGBA’], default ‘BW’
        # and Image.
        ##Image.save_render(filepath,scene)
        ##scene.render type RenderSettings
        ##https://docs.blender.org/api/2.79/bpy.types.RenderSettings.html
        ###bpy.types.RenderSettings
        ##.image_settings type ImageFormatSettings
        ##.resolution_x int
        ##.resolution_y int
        ##.use_file_extension
        
        if self.images_to_convert:
            fn = self.folder
            os.makedirs(os.path.join(fn,'images'))
            scene = bpy.context.scene
            image_settings = scene.render.image_settings
            save_rff = image_settings.file_format
            save_rcm = image_settings.color_mode
            image_settings.file_format = 'HDR'
            image_settings.color_mode = 'RGB'
            for key in self.images_to_convert.keys():
                (path_abs,path_ext,image) = self.images_to_convert[key]
                image.save_render(os.path.join(fn,'images/'+key+'.hdr'))
            # as a courtesy we restore settings we changed
            image_settings.file_format = save_rff
            image_settings.color_mode = save_rcm
            self.write_picture_cal()

    def make_rif(self):
        str_rif = """
#Rad Input File
DETAIL= Low
INDIRECT= 1
OCTREE= scene.oct
PICTURE= images/scene
QUALITY= Medium
RESOLUTION= 800
VARIABILITY= Low
ZONE= Interior -400 400 -500 500 -300 300
materials= materials.mat
scene= lights.lum Sun.rad scene.rad
view= nice -vf Camera.vf
"""
        return str_rif
    
    def write_rif(self):
        if False:
            # >rad scene.rif
            # not tested
            rfn = open(os.path.join(fn,"scene.rif"),"w+")
            str_rif = make_rif()
            rfn.write(str_rif)
            rfn.close()
        return

    def write_runs(self):
        # for windows users, convenience .bat
        # run0 - convert image textures to /image/*.hdr
        # run1 - oconv
        # run2 - rvu
        # run3 - pview
        # run4 - ra_bmp
        fn = self.folder
##        suffix = '.sh'
##        import platform
##        isWin = platform.system().lower() == 'windows'
##        if isWin:
##            suffix = '.bat'
        plats = ['.sh','.bat']
        rad_list = ["materials.mat", "lights.lum", "scene.rad"]
        if self.add_sky:
            rad_list.append("sky.mat")
            rad_list.append("sky.rad")
        rad_str = ' '.join(rad_list)
        for suffix in plats:
            rfn = open(os.path.join(fn,"run1"+suffix),"w+")
            rfn.write("oconv {} > scene.oct\n".format(rad_str))
            if suffix == '.bat': rfn.write("pause\n")
            rfn.close()
        
            cam_name = "Camera"
            if self.camname is not None:
                cam_name = self.camname
                
            rfn = open(os.path.join(fn,"run2"+suffix),"w+")
            rfn.write("rvu -vf %s.vf scene.oct\n" % cam_name)
            if suffix == '.bat': rfn.write("pause\n")
            rfn.close()


            rfn = open(os.path.join(fn,"run3"+suffix),"w+")
            rfn.write("rpict -vf %s.vf scene.oct > scene.hdr\n" % cam_name) 
            if suffix == '.bat': rfn.write("pause\n")
            rfn.close()

            rfn = open(os.path.join(fn,"run4"+suffix),"w+")
            rfn.write("ra_bmp -e auto scene.hdr > scene.bmp\n")
            if suffix == '.bat': rfn.write("pause\n")
            rfn.close()
        
        return
    


def menu_export(self, context):
    import os
    default_path = os.path.splitext(bpy.data.filepath)[0]
    self.layout.operator(RadianceExporter.bl_idname, text="BRADD27 Radiance Folder (*)").filepath = default_path

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()

