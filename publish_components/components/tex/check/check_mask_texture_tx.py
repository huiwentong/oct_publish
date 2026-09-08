# -*- coding: utf-8 -*-
import glob
import traceback
from pathlib import Path
import pymel.core as pm
import maya.utils as utils
from oct_maya.utils.maya_utils import texture_utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Mask / ID 类型贴图是否存在 tx 文件"""
    try:
        def glob_tex_files(path):
            """获取 UDIM 贴图文件"""
            return glob.glob(path.replace("<UDIM>", "*"))

        def get_aiimage_id_texture_data(ai_image):
            """获取连接到 Arnold ID 通道的 aiImage 贴图信息"""
            visited = set()
            def walk(node):
                node = pm.PyNode(node)
                if node.name() in visited:
                    return False
                visited.add(node.name())
                connections = pm.listConnections(node, source=False, destination=True, plugs=True,connections=True) or []
                for _, dst_plug in connections:
                    dst_node = dst_plug.node()
                    if not dst_node.nodeType().startswith("ai"):
                        continue
                    if "id" in dst_plug.longName().lower():
                        return True
                    if walk(dst_node):
                        return True

                return False

            if walk(ai_image):
                return {
                    "colorSpace": ai_image.colorSpace.get(),
                    "tex_path": ai_image.filename.get(),
                }
            return {}

        def get_tx_paths(tex_path, color_space, render_color_space):
            """获取贴图对应的 tx 文件路径"""
            src_name, suffix = tex_path.rsplit(".", 1)
            old_tx = src_name + ".tx"
            new_tx = "{}_{}_{}.{}.tx".format(src_name, color_space, render_color_space, suffix)

            return old_tx, new_tx

        def check():
            pm.loadPlugin("mtoa", quiet=True)
            pm.arnoldFlushCache(textures=True)
            render_color_space = pm.colorManagementPrefs(q=True, renderingSpaceName=True)

            for ai_image in pm.ls(type="aiImage"):
                tex_data = get_aiimage_id_texture_data(ai_image)

                if not tex_data:
                    continue

                color_space = tex_data["colorSpace"]
                tex_path = tex_data["tex_path"]

                if not tex_path:
                    continue

                if tex_path.lower().startswith("i:/projects"):
                    continue

                tex_path = tex_path.replace("<udim>", "<UDIM>")

                for texture in glob_tex_files(tex_path):
                    old_tx, new_tx = get_tx_paths(texture, color_space, render_color_space)
                    if Path(new_tx).is_file() or Path(old_tx).is_file():
                        continue
                    try:
                        logger.warning( "AUTO FIX: 生成 tx '{}'".format(texture))
                        texture_utils.single_file_make_tx(input_file=tex_path, colorspace=color_space)
                    except:
                        logger.warning("生成 tx 失败: '{}'\n Because ：{}".format(tex_path, traceback.format_exc()))

        utils.executeInMainThreadWithResult(check)

    except Exception:
        return traceback.format_exc()

