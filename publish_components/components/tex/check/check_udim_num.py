# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
import maya.app.general.fileTexturePathResolver as ftpr
from publish_components.utils.maya_utils.dialogs import ProgressUI

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 UDIM 贴图路径是否指向有效象限"""

    try:
        def check():
            mis_udims = {}
            shader_textures = process_data["d_shader_textures"]
            total = sum(len(textures) for textures in shader_textures.values())
            progress = ProgressUI(title=u"检查 UDIM 贴图路径是否指向有效象限", maximum=max(1, total),
                                  parent=parent_widget, enabled=bool(parent_widget), logger=logger)
            progress.show(u"准备检查 UDIM 路径...")

            try:
                for sg, textures in shader_textures.items():
                    for node_name, tex_info in textures.items():
                        progress.step(u"检查 UDIM 路径:\n{}".format(node_name))

                        if tex_info["type"] not in ("file", "aiImage"):
                            continue

                        tex_path = tex_info["tex_path"]
                        tex_pattern = tex_info["tex_pattern"]

                        if "<UDIM>" not in tex_pattern:
                            continue

                        if ftpr.findAllFilesForPattern(tex_path, None):
                            continue

                        mis_udims.setdefault(node_name, []).append(tex_info)

                progress.finish(u"UDIM 路径检查完成")

            finally:
                progress.close()

            return mis_udims

        missing_udims = utils.executeInMainThreadWithResult(check)
        process_data["missing_udim_paths"] = missing_udims

        if missing_udims:
            return (
                "UDIM 路径指向的 UV 贴图不存在，需要重指个有效UV\n" + "\n".join(
                    "  {} {}".format(node_name, tex_infos[0]["tex_path"])
                    for node_name, tex_infos in missing_udims.items()
                )
            )

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """将无效 UDIM 路径重新指向实际存在的象限贴图"""


    try:
        def do_fix():
            asset_textures = process_data["d_asset_tex"]
            missing_udims = process_data["missing_udim_paths"]

            valid_paths = {
                node_name: sorted(textures)[0]
                for node_name, textures in asset_textures.items() if textures
            }

            progress = ProgressUI(title=u"修复 UDIM 路径", maximum=max(1, len(missing_udims)),
                                  parent=parent_widget, enabled=bool(parent_widget), logger=logger)
            progress.show(u"准备修复 UDIM 路径...")

            try:
                for node_name in sorted(missing_udims):
                    progress.step(u"修复 UDIM 路径:\n{}".format(node_name))

                    if node_name not in valid_paths:
                        continue

                    valid_path = valid_paths[node_name]
                    node = pm.PyNode(node_name)
                    node.fileTextureName.set(valid_path)

                    for tex_info in missing_udims[node_name]:
                        tex_info["tex_path"] = valid_path

                    logger.warning("AUTO FIX: UDIM 路径 '{}' -> '{}'".format(node_name, valid_path))

                progress.finish(u"UDIM 路径修复完成")

            finally:
                if progress:
                    progress.close()

        utils.executeInMainThreadWithResult(do_fix)

    except Exception:
        return traceback.format_exc()
