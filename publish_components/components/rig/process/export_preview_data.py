#!/usr/bin/env python  
# -*- coding:utf-8 -*-
""" 
@author:jiongwan
@team : Octmedia TD Department
@file: export_preview_data.py 
@time: 2023/01/16
@contact: wanjw126@126.com
"""
import os,sys
import glob
import json
import traceback

import pymel.core as pm

from oct.pipeline import path
from oct_maya.utils.maya_utils.camera import export_tmp_cam, create_tmp_camera


class PreviewDataGenerator():
    def __init__(self, sourceimages_path=None):
        self.sourceimages_path = sourceimages_path
        self.sel_node = "|Root_grp|Geo_grp|high"

        self._color_input_template = {"_type": "",  # file or color layeredTexture
                                      "fileTextureName": "",
                                      "repeat": [],  # {repeatU, repeatV]
                                      "offset": []  # {offsetU, offsetV]
                                      }

        self._shader_template = {"_type": "",  # lambert, bline, ...
                                 "_assign_shapes": [],
                                 "diffuse": 0.0,  # float
                                 "color": [0.8, 0.8, 0.8] ,  # [0.8, 0.8, 0.8] or self._color_input_template
                                 "transparency": [],
                                 "opacity": [],
                                 "specularRollOff": 0.0,
                                 "eccentricity": 0.0,
                                 "specularColor": [],
                                 "sp_ior": 0.0,
                                 }

        self._basics_lambert_data = self.__get_basics_lambert_data()

    def __get_real_tex_file(self, tex_file):
        # Find a tex from the specified tex path
        if not self.sourceimages_path:
            return tex_file

        pub_tex_file = os.path.join(self.sourceimages_path, os.path.basename(tex_file)).replace("\\", "/")
        if tex_file == pub_tex_file:
            return tex_file

        elif ".<f>." in pub_tex_file:  # ...\sourceimages\L_UpperLid.<f>.png
            tex_pattern = pub_tex_file.replace('.<f>.', '.*.')  # ...\sourceimages\L_UpperLid.*.png
            matched_texs = glob.glob(tex_pattern)
            if matched_texs:
                return tex_pattern.replace('.*.', '.<f>.')  # I:\...\sourceimages\L_UpperLid.<f>.png
        else:
            # copy tex to publish path
            if os.path.exists(pub_tex_file):
                return pub_tex_file

        return tex_file

    def get_color_input_data(self, color_attr):
        if not color_attr.inputs():
            return color_attr.get()  # return base color
        else:
            color_input_node = color_attr.inputs()[0]

            file_node = None
            if color_input_node.type() == "file":
                file_node = color_input_node
            elif color_input_node.type() == "layeredTexture":
                if color_input_node.inputs():
                    file_node = color_input_node.inputs()[0]

            if file_node:
                data = self._color_input_template.copy()
                data["_type"] = file_node.type()
                data["fileTextureName"] = self.__get_real_tex_file(file_node.attr('computedFileTextureNamePattern').get())

                if file_node.inputs(type='place2dTexture'):
                    p2d_node = file_node.inputs(type='place2dTexture')[0]
                    data["repeat"] = (p2d_node.repeatU.get(), p2d_node.repeatV.get())
                    data["offset"] = (p2d_node.offsetU.get(), p2d_node.offsetV.get())
                    return data

        return [0.8, 0.8, 0.8]


    def __get_basics_lambert_data(self):
        # This is used when shape has no shader
        data = self._shader_template.copy()
        shader_node = pm.PyNode('lambert1')
        data["_type"] = "basics_lambert"
        data["diffuse"] = shader_node.attr('diffuse').get()
        data["color"] = self.get_color_input_data(shader_node.attr('color'))
        data["transparency"] = shader_node.attr('transparency').get()
        data["opacity"] = (1.0 - data["transparency"][0],
                           1.0 - data["transparency"][1],
                           1.0 - data["transparency"][2])
        data["specularRollOff"] = 0
        data["eccentricity"] = 0.2
        data["specularColor"] = [0.0, 0.0, 0.0]
        data["sp_ior"] = 1.5

        return data

    def get_shapes(self):
        shapes = []
        if pm.objExists(self.sel_node):
            shapes = pm.PyNode(self.sel_node).listRelatives(allDescendents=True,
                                                            type='mesh',
                                                            noIntermediate=True)
        return shapes

    def get_shader_data(self, shader_node):
        # surface shader
        if not shader_node.type() in ('lambert', 'blinn'):
            return self._basics_lambert_data

        data = self._shader_template.copy()
        data["_type"] = shader_node.type()
        data["diffuse"] = shader_node.attr('diffuse').get()
        data["color"] = self.get_color_input_data(shader_node.attr('color'))
        data["transparency"] = shader_node.attr('transparency').get()
        data["opacity"] = [1.0 - data["transparency"][0],
                           1.0 - data["transparency"][1],
                           1.0 - data["transparency"][2]]

        if shader_node.type() == 'lambert':
            data["specularRollOff"] = 0
            data["eccentricity"] = 0.2
            data["specularColor"] = [0.0, 0.0, 0.0]
            data["sp_ior"] = 1.0

        elif shader_node.type() == 'blinn':
            data["specularRollOff"] = shader_node.attr('specularRollOff').get()
            data["eccentricity"] = shader_node.attr('eccentricity').get()
            data["specularColor"] = self.get_color_input_data(shader_node.attr('specularColor'))
            data["sp_ior"] = 3.0

        return data

    def get_data(self):
        shader_shapes_map = {}  # all used shading engines
        for shape in self.get_shapes():
            se_nodes = shape.listConnections(type='shadingEngine')
            for se_n in se_nodes:
                shader_nodes = se_n.attr('surfaceShader').inputs()
                for shader_n in shader_nodes:
                    if shader_n in shader_shapes_map:
                        shader_shapes_map[shader_n].append(shape.fullPath())
                    else:
                        shader_shapes_map[shader_n] = [shape.fullPath()]

        data = {}
        # {shader: self._shader_template}
        for shader, shapes in shader_shapes_map.items():
            shader_data = self.get_shader_data(shader)
            shader_data["_assign_shapes"] = shapes
            data[shader.name()] = shader_data

        return data

    def write_json(self, json_file):
        data = self.get_data()

        # Compatible with python 2 and 3
        if sys.version_info[0] == 2:
            with open(json_file, 'w') as f:
                json.dump(data, f,
                          sort_keys=True,
                          indent=4,
                          ensure_ascii=False,
                          encoding="utf-8")
        else:
            with open(json_file, 'w') as f:
                json.dump(data, f,
                          sort_keys=True,
                          indent=4,
                          ensure_ascii=False)


class StdProcess():

    def __init__(self, dialog):
        self.dialog = dialog
        self.process_name = u"导出预览材质数据及预览相机"
        self.description = u"导出预览材质数据及预览相机"
        return

    def proceed(self):
        import pymel.core as pm
        try:
            # export pre camera
            #from toolsets.tools.srf.gene import export_asset_cam as eac

            asset_info = self.dialog.d_assets_info[self.dialog.entity['code']]
            # asset_info['v_dir_imgs']  I:\...\sourceimages
            pdg = PreviewDataGenerator(sourceimages_path=asset_info['v_dir_imgs'])

            json_file = os.path.join(self.dialog.version_dir, 'preview_shaders.json').replace('\\', '/')
            pdg.write_json(json_file)

            pre_cam = create_tmp_camera()
            export_tmp_cam(pre_cam, self.dialog.version_dir)

            pm.delete(pre_cam)

            return ""
        except:
            return traceback.format_exc()

    def get_process_name(self):
        return self.process_name

    def get_description(self):
        return self.description