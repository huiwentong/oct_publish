# -*- coding: utf-8 -*-
import os
import traceback
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.maya_utils import get_upstream_nodes

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """收集 Surface Shader、贴图、材质颜色等信息。"""

    try:
        DEFAULT_SE = {"initialParticleSE", "initialShadingGroup"}
        TEXTURE_TYPES = {"file", "aiImage"}
        def get_texture_nodes(node):
            """获取节点上游所有 file / aiImage 贴图节点名。"""
            nodes = []
            get_upstream_nodes.iter_upstream(node.name(), nodes)
            return [
                name for name in nodes
                if pm.nodeType(name) in TEXTURE_TYPES
            ]

        def get_surface_color(shader):
            """
            获取材质基础颜色以及对应颜色贴图。
            优先寻找文件名中包含 basecolor / color 的贴图。
            """
            default_color = (0.5, 0.5, 0.5)

            if shader.hasAttr("color"):
                attr = shader.color
            elif shader.hasAttr("baseColor"):
                attr = shader.baseColor
            elif shader.nodeType() == "aiLayerShader":
                # Layer Shader 递归寻找内部 Surface Shader
                for node in shader.listConnections(s=True, d=False):
                    if node.nodeType() in ("aiStandardSurface", "aiLayerShader"):
                        return get_surface_color(node)

                return default_color, ""
            else:
                return default_color, ""

            color = attr.get()

            # 从颜色属性开始寻找上游贴图
            nodes = []
            for node in attr.listConnections(s=True, d=False):
                nodes.append(node.name())
                get_upstream_nodes.iter_upstream(node.name(), nodes)

            textures = []
            for name in nodes:
                node = pm.PyNode(name)

                if node.nodeType() == "file":
                    textures.append(
                        node.computedFileTextureNamePattern.get()
                    )
                elif node.nodeType() == "aiImage":
                    textures.append(
                        node.filename.get()
                    )

            if not textures:
                return color, ""

            # 优先使用明显属于 BaseColor 的贴图
            for keyword in ("basecolor", "color"):
                for path in textures:
                    if keyword in os.path.basename(path).lower():
                        return color, path

            return color, textures[0]

        def get_transparency(shader):
            """统一获取 Arnold transmission / Maya transparency。"""
            if shader.hasAttr("transmission"):
                value = max(0.0, min(1.0, shader.transmission.get()))
                return value, value, value

            if shader.hasAttr("transparency"):
                return shader.transparency.get()

            return 0, 0, 0

        def get_high_shaders():
            """获取 high 模型实际使用到的 ShadingEngine。"""
            high = process_data.get("high", "|Root_grp|Geo_grp|high")
            shaders = set()

            for mesh in pm.listRelatives(high, ad=True, type="mesh"):
                for node in pm.listConnections(mesh, s=False, d=True):
                    if node.nodeType() == "shadingEngine":
                        if node.name() not in DEFAULT_SE:
                            shaders.add(node.name())

            return list(shaders)

        def get_texture_data(node):
            """整理单个 file / aiImage 节点的数据。"""
            if node.nodeType() == "file":
                pattern = node.computedFileTextureNamePattern.get()

                return {
                    "type": "file",
                    "tex_path": node.fileTextureName.get(),
                    "tex_pattern": os.path.basename(pattern).replace("<udim>", "<UDIM>"),
                    "cs": node.colorSpace.get(),
                    "tiling_mode": node.uvTilingMode.get(),
                }

            path = node.filename.get().replace("<udim>", "<UDIM>")

            return {
                "type": "aiImage",
                "tex_path": path,
                "tex_pattern": os.path.basename(path),
                "cs": node.colorSpace.get(),
                "tiling_mode": 3 if "<UDIM>" in path else 0,
            }

        def collect():
            """必须在 Maya Main Thread 中执行。"""
            surface_shaders = {}
            shader_textures = {}
            for se in pm.ls(type="shadingEngine"):
                if se.name() in DEFAULT_SE:
                    continue
                se_name = se.name()
                assigned = pm.sets(se, q=True) or []
                surface = se.surfaceShader.listConnections(s=True, d=False)
                displacement = se.displacementShader.listConnections(s=True, d=False)
                data = {
                    "se": se,
                    "shader": None,
                    "shader_disp": displacement[0].name() if displacement else None,
                    "assigned": assigned,
                    "geo": list({str(item).split(".f[")[0] for item in assigned}),
                    "tex": [],
                    "udims": {},
                    "color": None,
                    "color_tex": "",
                    "trans": None,
                }

                if surface:
                    shader = surface[0]
                    data["shader"] = shader.name()
                    data["tex"] = get_texture_nodes(se)
                    data["color"], data["color_tex"] = get_surface_color(shader)
                    data["trans"] = get_transparency(shader)

                surface_shaders[se_name] = data
                # ShadingEngine -> Texture Node -> Texture Info
                shader_textures[se_name] = {node_name: get_texture_data(pm.PyNode(node_name)) for node_name in data["tex"]}

            process_data["d_srf_shaders"] = surface_shaders
            process_data["d_shader_textures"] = shader_textures
            process_data["shaders"] = get_high_shaders()
            return surface_shaders, shader_textures, get_high_shaders()

        utils.executeInMainThreadWithResult(collect)

    except Exception:
        return traceback.format_exc()
