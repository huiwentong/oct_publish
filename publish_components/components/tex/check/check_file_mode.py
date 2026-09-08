# -*- coding: utf-8 -*-

import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查贴图 UV Tiling Mode 是否为 Off 或 UDIM"""
    try:
        def check():
            er_nodes = []
            for file_node in pm.ls(type="file"):
                if file_node.uvTilingMode.get() not in {0, 3}:
                    er_nodes.append(file_node.nodeName())
            return er_nodes

        error_nodes = utils.executeInMainThreadWithResult(check)

        if error_nodes:
            return "部分贴图节点 UV Tiling Mode 既不是 Off 也不是 UDIM：\n{}".format("\n".join(error_nodes))

    except Exception:
        return traceback.format_exc()
