# -*- coding: utf-8 -*-

import os
import re
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 UDIM 贴图文件名是否规范"""
    try:
        def check():
            er_nodes = []

            for file_node in pm.ls(type="file"):
                if file_node.uvTilingMode.get() != 3:
                    continue
                filename = os.path.basename(file_node.fileTextureName.get())

                if '<UDIM>' in filename or re.search(r"[\_\.]10\d\d[\_\.]", filename):
                    continue
                er_nodes.append({
                    "node": file_node.name(),
                    "filename": filename,
                })

            return er_nodes

        error_nodes = utils.executeInMainThreadWithResult(check)
        if error_nodes:
            process_data["invalid_udim_texture_nodes"] = error_nodes
            return "UDIM 贴图调用的贴图名不规范：\n{}".format(
                "\n".join("{}: {}".format(item["node"], item["filename"]) for item in error_nodes))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """将文件名不规范的 UDIM 贴图改为 Off"""
    try:
        def repair():
            error_nodes = process_data.get("invalid_udim_texture_nodes", [])
            for item in error_nodes:
                node = pm.PyNode(item["node"])
                node.uvTilingMode.set(0)
                logger.warning("AUTO FIX: 设置 '{}' UV Tiling Mode 为 Off".format(node.name()))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
