#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import glob
import json
import math
import traceback
import pymel.core as pm
import maya.mel as mel
import maya.utils as utils

from oct_maya.utils.maya_utils.camera import export_tmp_cam, create_tmp_camera


def main(submit_data, process_data, parent_widget=None, logger=None):
    """导出预览材质数据及预览相机"""
    try:
        _COLOR_INPUT_TEMPLATE = {
            "_type": "",
            "fileTextureName": "",
            "repeat": [],
            "offset": [],
        }
        _SHADER_TEMPLATE = {
            "_type": "",
            "_assign_shapes": [],
            "diffuse": 0.0,
            "color": [0.8, 0.8, 0.8],
            "transparency": [],
            "opacity": [],
            "specularRollOff": 0.0,
            "eccentricity": 0.0,
            "specularColor": [],
            "sp_ior": 0.0,
        }

        def _get_real_tex_file(tex_file, sourceimages_path):
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
            elif os.path.exists(pub):
                return pub
            return tex_file

        def _get_color_input_data(color_attr, sourceimages_path):
            if not color_attr.inputs():
                return color_attr.get()

            color_input_node = color_attr.inputs()[0]
            file_node = None

            if color_input_node.type() == "file":
                file_node = color_input_node
            elif color_input_node.type() == "layeredTexture" and color_input_node.inputs():
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
                    shader_node.attr("specularColor"),
                    sourceimages_path,
                )
                data["sp_ior"] = 3.0

            return data

        def _get_data(sourceimages_path):
            sel_node = "|Root_grp"
            shapes = []

            if pm.objExists(sel_node):
                shapes = pm.PyNode(sel_node).listRelatives(
                    allDescendents=True,
                    type="mesh",
                    noIntermediate=True,
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
            data = _get_data(sourceimages_path)

            if sys.version_info[0] == 2:
                with open(json_file, "w") as f:
                    json.dump(
                        data,
                        f,
                        sort_keys=True,
                        indent=4,
                        ensure_ascii=False,
                        encoding="utf-8",
                    )
            else:
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(
                        data,
                        f,
                        sort_keys=True,
                        indent=4,
                        ensure_ascii=False,
                    )

        def _create_tmp_camera_batch(
            cam_name="pre_cam",
            offset_ty=0,
            offset_tz=2,
            offset_rx=0,
        ):
            if pm.objExists(cam_name):
                pm.delete(cam_name)

            root = "|Root_grp"
            if not pm.objExists(root):
                raise RuntimeError("创建预览相机失败，场景中不存在 |Root_grp")

            pre_cam, cam_shape = pm.camera()
            pre_cam = pm.rename(pre_cam, cam_name)
            cam_shape = pre_cam.getShape()

            vertical_aperture = cam_shape.verticalFilmAperture.get()
            cam_shape.horizontalFilmAperture.set(vertical_aperture * 1.365)
            cam_shape.lensSqueezeRatio.set(1)

            bbox = pm.exactWorldBoundingBox(root)
            min_x, min_y, min_z = bbox[0:3]
            max_x, max_y, max_z = bbox[3:6]

            center_x = (min_x + max_x) / 2.0
            center_y = (min_y + max_y) / 2.0
            width = max(max_x - min_x, 0.001)
            height = max(max_y - min_y, 0.001)

            focal_length = float(cam_shape.focalLength.get())
            horizontal_aperture_mm = float(cam_shape.horizontalFilmAperture.get()) * 25.4
            vertical_aperture_mm = float(cam_shape.verticalFilmAperture.get()) * 25.4

            horizontal_fov = 2.0 * math.atan(horizontal_aperture_mm / (2.0 * focal_length))
            vertical_fov = 2.0 * math.atan(vertical_aperture_mm / (2.0 * focal_length))

            distance_x = (width / 2.0) / math.tan(horizontal_fov / 2.0)
            distance_y = (height / 2.0) / math.tan(vertical_fov / 2.0)
            distance = max(distance_x, distance_y) * 1.1

            pre_cam.translateX.set(center_x)
            pre_cam.translateY.set(center_y + offset_ty)
            pre_cam.translateZ.set(max_z + distance + offset_tz)
            pre_cam.rotateX.set(offset_rx)
            pre_cam.rotateY.set(0)
            pre_cam.rotateZ.set(0)

            return pre_cam

        def _export_tmp_cam_batch(
            pre_cam,
            tmp_cam_root="",
            tmp_cam_dir="tmp_cam",
            tmp_cam_name="pre_cam.abc",
            frame=(1, 1),
        ):
            if not pm.pluginInfo("AbcExport.mll", q=True, loaded=True):
                pm.loadPlugin("AbcExport.mll", quiet=True)

            file_path = str(pm.sceneName())
            file_folder = os.path.dirname(file_path)

            if not tmp_cam_root:
                cam_cache_path = os.path.join(
                    file_folder,
                    tmp_cam_dir,
                    tmp_cam_name,
                ).replace("\\", "/")
            else:
                cam_cache_path = os.path.join(
                    tmp_cam_root,
                    tmp_cam_dir,
                    tmp_cam_name,
                ).replace("\\", "/")

            cam_cache_dir = os.path.dirname(cam_cache_path)
            if not os.path.exists(cam_cache_dir):
                os.makedirs(cam_cache_dir)

            export_command = (
                'AbcExport -j "-frameRange {} {} -worldSpace '
                '-dataFormat ogawa -root {} -file {}"'
            ).format(
                frame[0],
                frame[1],
                pre_cam.longName(),
                cam_cache_path,
            )

            if logger:
                logger.info(f"Batch export preview camera: {export_command}")
            else:
                print(export_command)

            mel.eval(export_command)

            if not os.path.isfile(cam_cache_path):
                raise RuntimeError(f"预览相机导出失败: {cam_cache_path}")

            return cam_cache_path

        def process():
            v_dir_imgs = process_data["v_dir_imgs"]
            version_dir = process_data.get("version_dir", "")
            json_file = os.path.join(
                version_dir,
                "preview_shaders.json",
            ).replace("\\", "/")

            _write_json(json_file, v_dir_imgs)

            pre_cam = None
            try:
                if pm.about(batch=True):
                    if logger:
                        logger.info("当前为 Maya Batch 模式，使用无视口方式生成预览相机")
                    pre_cam = _create_tmp_camera_batch()
                    _export_tmp_cam_batch(pre_cam, version_dir)
                else:
                    pre_cam = create_tmp_camera()
                    export_tmp_cam(pre_cam, version_dir)
            finally:
                if pre_cam is not None and pm.objExists(pre_cam):
                    pm.delete(pre_cam)

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except Exception:
        return traceback.format_exc()