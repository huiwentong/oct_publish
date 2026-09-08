# -*- coding: utf-8 -*-
import os
import shutil
import traceback
import pymel.core as pm
import maya.utils as utils
from pathlib import Path
from publish_components.utils import maya_utils
from publish_components.utils.maya_utils import get_uv_shells
from publish_components.utils.maya_utils import create_ml_json

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查贴图是否存在，以及 UDIM 是否覆盖 Mesh 使用的 UV 象限"""

    try:
        def get_mesh_udims(mesh):
            """获取 Mesh 使用的 UDIM"""
            bbox = pm.polyEvaluate(mesh, boundingBox2d=True)
            if not get_uv_shells.cross_udim(bbox):
                return [get_uv_shells.get_udim_center(bbox)]

            udims = set()

            for uv_id, shell_bbox in get_uv_shells.get_shells(mesh).items():
                if type(shell_bbox) is not tuple:
                    print("Invalid UV:", uv_id, shell_bbox)
                    continue
                udims.update(get_uv_shells.get_udim_range(shell_bbox))

            return sorted(udims)

        def add_texture(texture_data, node_name, tex_path, mesh_name, color_space):
            """记录贴图及使用该贴图的 Mesh"""
            tex_info = texture_data.setdefault(node_name, {}).setdefault(tex_path, {
                                                                                    "mesh": [],
                                                                                    "md5": None,
                                                                                    "img_v_dir": None,
                                                                                    "colorSpace": color_space
                                                                                    })

            tex_info["mesh"].append(mesh_name)

        def add_shader_udim(surface_shaders, sg, mesh_name, udim):
            """记录 ShadingEngine 对应 Mesh 使用的 UDIM"""
            sg_name = sg.name()
            if sg_name not in surface_shaders:
                return

            surface_shaders[sg_name]["udims"].setdefault(mesh_name, []).append(udim)

        def collect_mesh_textures(mesh, texture_data, shader_textures, surface_shaders):
            """收集一个 Mesh 使用的所有贴图"""
            mesh_name = mesh.name()
            mesh_udims = None

            shading_groups = pm.listConnections(mesh, source=False, destination=True, type="shadingEngine")
            for sg in shading_groups:
                for node_name, tex_info in shader_textures[sg.name()].items():
                    tex_path = tex_info["tex_path"]
                    tex_pattern = tex_info["tex_pattern"]
                    color_space = tex_info["cs"]

                    if "<UDIM>" not in tex_pattern:
                        add_texture(texture_data, node_name, tex_path, mesh_name, color_space)
                        continue

                    # 一个 Mesh 最多计算一次 UDIM
                    if mesh_udims is None:
                        mesh_udims = get_mesh_udims(mesh)

                    tex_dir = os.path.dirname(tex_path)
                    for udim in mesh_udims:
                        udim_path = os.path.join(tex_dir, tex_pattern.replace("<UDIM>", str(udim)))
                        add_texture(texture_data, node_name, udim_path, mesh_name, color_space)
                        add_shader_udim(surface_shaders, sg, mesh_name, udim)

        def collect_asset_textures(shader_textures, surface_shaders):
            """收集资产实际需要的所有贴图"""
            texture_data = {}
            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
            meshes = pm.listRelatives(n_high, ad=True, type="mesh")
            for mesh in meshes:
                collect_mesh_textures(mesh, texture_data, shader_textures, surface_shaders)
            return texture_data

        def find_missing_textures(texture_data):
            """获取不存在的贴图文件"""
            mis_textures = []
            exists_cache = {}

            for node_name, textures in texture_data.items():
                for tex_path, tex_info in textures.items():
                    if tex_path not in exists_cache:
                        exists_cache[tex_path] = os.path.isfile(tex_path)
                    if exists_cache[tex_path]:
                        continue

                    mis_textures.append(
                        {
                            "node": node_name,
                            "path": tex_path,
                            "meshes": tex_info["mesh"],
                        }
                    )

            return mis_textures

        def check():
            shader_textures = process_data["d_shader_textures"]
            surface_shaders = process_data["d_srf_shaders"]
            texture_data = collect_asset_textures(shader_textures, surface_shaders)
            return texture_data, find_missing_textures(texture_data)

        d_asset_tex, missing_textures = utils.executeInMainThreadWithResult(check)

        process_data["d_asset_tex"] = d_asset_tex
        process_data["missing_texture_files"] = missing_textures

        if missing_textures:
            return "\n".join(
                "贴图节点 {} (被几何体 {} 使用) 无法找到图片：\n{}".format(
                    item["node"], ",".join(item["meshes"]), item["path"])
                    for item in missing_textures)

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """为缺失的 UDIM 象限补黑色、灰色或 Normal 图片"""

    try:
        error_files = []
        move_files = []

        def get_fill_texture(tex_path):
            """获取缺失贴图对应的补块图片"""
            tex_ext = tex_path.rsplit(".", 1)[-1]
            filename = os.path.basename(tex_path)

            module_dir = Path(maya_utils.__file__).resolve().parent / "textures"

            if tex_ext.lower() == "exr":
                return os.path.join(module_dir, "grey.exr")

            if "normal" in filename.lower():
                return os.path.join(module_dir, "NOR.tif")

            return os.path.join(module_dir, "black.{}".format(tex_ext))

        def create_temp_texture(src, tex_path, version_dir):
            """创建临时补块贴图，并返回需要搬运的文件"""
            version_root = os.path.dirname(version_dir.rstrip("/"))
            tmp_file = os.path.join(version_root, "tmp", os.path.basename(tex_path))
            tmp_tx = tmp_file.rsplit(".", 1)[0] + ".tx"
            tex_tx = tex_path.rsplit(".", 1)[0] + ".tx"

            if not os.path.exists(os.path.dirname(tmp_file)):
                os.makedirs(os.path.dirname(tmp_file))

            if not os.path.exists(tmp_file):
                shutil.copy(src, tmp_file)
                src_tx = src.rsplit(".", 1)[0] + ".tx"
                shutil.copy(src_tx, tmp_tx)

            return [(tmp_file, tex_path), (tmp_tx, tex_tx)]

        for item in process_data.get("missing_texture_files", []):
            tex_path = item["path"]
            src = get_fill_texture(tex_path)

            if not os.path.isfile(src):
                error_files.append("找不到对应格式的色块文件: {}".format(os.path.basename(src)))
                continue

            try:
                shutil.copy(src, tex_path)
                logger.warning("AUTO FIX: 补充缺失贴图 '{}'".format(tex_path))

            except Exception:
                move_files.extend(create_temp_texture(src, tex_path, process_data["version_dir_old"]))

        if move_files:
            create_ml_json.move_link_dirs(process_data["version_name"] + ".fix_udim_tiles", move_files, [])

        if error_files:
            error = "自动修复无法解决:\n{}".format("\n".join(error_files))
            logger.error(error)
            return error

    except Exception:
        return traceback.format_exc()
