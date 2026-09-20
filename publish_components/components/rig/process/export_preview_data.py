#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import glob
import json
import traceback
import pymel.core as pm
import maya.utils as utils

from oct_maya.utils.maya_utils.camera import export_tmp_cam, create_tmp_camera


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main(submit_data, process_data, parent_widget=None, logger=None):
    """
    导出预览材质数据及预览相机
    """
    try:
        # ---------------------------------------------------------------------------
        # 模板常量（原类属性提升为模块常量）
        # ---------------------------------------------------------------------------

        _COLOR_INPUT_TEMPLATE = {
            "_type": "",  # file or color layeredTexture
            "fileTextureName": "",
            "repeat": [],  # [repeatU, repeatV]
            "offset": [],  # [offsetU, offsetV]
        }

        _SHADER_TEMPLATE = {
            "_type": "",  # lambert, blinn, ...
            "_assign_shapes": [],
            "diffuse": 0.0,
            "color": [0.8, 0.8, 0.8],  # 或 _COLOR_INPUT_TEMPLATE
            "transparency": [],
            "opacity": [],
            "specularRollOff": 0.0,
            "eccentricity": 0.0,
            "specularColor": [],
            "sp_ior": 0.0,
        }

        # ---------------------------------------------------------------------------
        # 内部辅助函数
        # ---------------------------------------------------------------------------

        def _get_real_tex_file(tex_file, sourceimages_path):
            """将贴图路径替换为 sourceimages 目录下的实际文件。"""
            if not sourceimages_path:
                return tex_file

            pub = os.path.join(sourceimages_path, os.path.basename(tex_file)).replace("\\", "/")
            if tex_file == pub:
                return tex_file

            if ".<f>." in pub:
                pattern = pub.replace(".<f>.", ".*.")
                matched = glob.glob(pattern)
                if matched:
                    return pattern.replace(".*.", ".<f>.")
            else:
                if os.path.exists(pub):
                    return pub

            return tex_file

        def _get_color_input_data(color_attr, sourceimages_path):
            """解析 color 属性，返回纯色值或 file/layeredTexture 数据。"""
            if not color_attr.inputs():
                return color_attr.get()

            color_input_node = color_attr.inputs()[0]

            file_node = None
            if color_input_node.type() == "file":
                file_node = color_input_node
            elif color_input_node.type() == "layeredTexture":
                if color_input_node.inputs():
                    file_node = color_input_node.inputs()[0]

            if file_node:
                data = _COLOR_INPUT_TEMPLATE.copy()
                data["_type"] = file_node.type()
                data["fileTextureName"] = _get_real_tex_file(
                    file_node.attr("computedFileTextureNamePattern").get(),
                    sourceimages_path,
                )

                if file_node.inputs(type="place2dTexture"):
                    p2d = file_node.inputs(type="place2dTexture")[0]
                    data["repeat"] = [p2d.repeatU.get(), p2d.repeatV.get()]
                    data["offset"] = [p2d.offsetU.get(), p2d.offsetV.get()]

                return data

            return [0.8, 0.8, 0.8]

        def _get_basics_lambert_data(sourceimages_path):
            """获取默认 lambert1 的材质数据（用于无 shader 的 shape）。"""
            data = _SHADER_TEMPLATE.copy()
            shader = pm.PyNode("lambert1")

            data["_type"] = "basics_lambert"
            data["diffuse"] = shader.attr("diffuse").get()
            data["color"] = _get_color_input_data(shader.attr("color"), sourceimages_path)
            data["transparency"] = shader.attr("transparency").get()
            data["opacity"] = [
                1.0 - data["transparency"][0],
                1.0 - data["transparency"][1],
                1.0 - data["transparency"][2],
            ]
            data["specularRollOff"] = 0
            data["eccentricity"] = 0.2
            data["specularColor"] = [0.0, 0.0, 0.0]
            data["sp_ior"] = 1.5

            return data

        def _get_shader_data(shader_node, sourceimages_path, basics_lambert_data):
            """解析指定 shader 节点，返回材质数据字典。"""
            if shader_node.type() not in ("lambert", "blinn"):
                return basics_lambert_data

            data = _SHADER_TEMPLATE.copy()
            data["_type"] = shader_node.type()
            data["diffuse"] = shader_node.attr("diffuse").get()
            data["color"] = _get_color_input_data(shader_node.attr("color"), sourceimages_path)
            data["transparency"] = shader_node.attr("transparency").get()
            data["opacity"] = [
                1.0 - data["transparency"][0],
                1.0 - data["transparency"][1],
                1.0 - data["transparency"][2],
            ]

            if shader_node.type() == "lambert":
                data["specularRollOff"] = 0
                data["eccentricity"] = 0.2
                data["specularColor"] = [0.0, 0.0, 0.0]
                data["sp_ior"] = 1.0

            elif shader_node.type() == "blinn":
                data["specularRollOff"] = shader_node.attr("specularRollOff").get()
                data["eccentricity"] = shader_node.attr("eccentricity").get()
                data["specularColor"] = _get_color_input_data(
                    shader_node.attr("specularColor"), sourceimages_path
                )
                data["sp_ior"] = 3.0

            return data

        def _get_data(sourceimages_path):
            """收集场景中所有 shape 的 shader 数据。"""
            sel_node = "|Root_grp|Geo_grp|high"

            shapes = []
            if pm.objExists(sel_node):
                shapes = pm.PyNode(sel_node).listRelatives(
                    allDescendents=True, type="mesh", noIntermediate=True
                )

            basics_lambert = _get_basics_lambert_data(sourceimages_path)

            shader_shapes_map = {}
            for shape in shapes:
                se_nodes = shape.listConnections(type="shadingEngine")
                for se_n in se_nodes:
                    for shader_n in se_n.attr("surfaceShader").inputs():
                        if shader_n in shader_shapes_map:
                            shader_shapes_map[shader_n].append(shape.fullPath())
                        else:
                            shader_shapes_map[shader_n] = [shape.fullPath()]

            data = {}
            for shader, shape_list in shader_shapes_map.items():
                sd = _get_shader_data(shader, sourceimages_path, basics_lambert)
                sd["_assign_shapes"] = shape_list
                data[shader.name()] = sd

            return data

        def _write_json(json_file, sourceimages_path):
            """生成材质数据并写入 JSON 文件。"""
            data = _get_data(sourceimages_path)

            if sys.version_info[0] == 2:
                with open(json_file, "w") as f:
                    json.dump(data, f, sort_keys=True, indent=4,
                              ensure_ascii=False, encoding="utf-8")
            else:
                with open(json_file, "w") as f:
                    json.dump(data, f, sort_keys=True, indent=4,
                              ensure_ascii=False)

        def process():
            v_dir_imgs = process_data["v_dir_imgs"]
            version_dir = process_data.get("version_dir", "")

            json_file = os.path.join(version_dir, "preview_shaders.json").replace("\\", "/")
            _write_json(json_file, v_dir_imgs)

            pre_cam = create_tmp_camera()
            export_tmp_cam(pre_cam, version_dir)
            pm.delete(pre_cam)
            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except Exception:
        return traceback.format_exc()
