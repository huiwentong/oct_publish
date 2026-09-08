# -*- coding: utf-8 -*-

import traceback

import pymel.core as pm
import maya.utils as utils




def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 UDIM 贴图连接的 place2dTexture 是否被修改"""
    try:
        PLACE2D_DEFAULT_ATTRS = {
            "coverageU": 1.0,
            "coverageV": 1.0,
            "translateFrameU": 0.0,
            "translateFrameV": 0.0,
            "rotateFrame": 0.0,
            "mirrorU": 0,
            "mirrorV": 0,
            "wrapU": 1,
            "wrapV": 1,
            "stagger": 0,
            "repeatU": 1.0,
            "repeatV": 1.0,
            "offsetU": 0.0,
            "offsetV": 0.0,
            "rotateUV": 0.0,
            "noiseU": 0.0,
            "noiseV": 0.0,
        }
        def is_place2d_untouched(node):
            """检查 place2dTexture 参数是否保持默认值"""
            return all(
                node.getAttr(attr) == value
                for attr, value in PLACE2D_DEFAULT_ATTRS.items()
            )

        def check():
            er_nodes = set()

            for file_node in pm.ls(type="file"):
                if file_node.uvTilingMode.get() != 3:
                    continue

                place2d_nodes = pm.listConnections(file_node.uvCoord, source=True, destination=False) or []
                for node in place2d_nodes:
                    if (
                        node.nodeType() == "place2dTexture"
                        and not is_place2d_untouched(node)
                    ):
                        er_nodes.add(node.nodeName())

            return er_nodes

        error_nodes = utils.executeInMainThreadWithResult(check)


        if error_nodes:
            process_data["udim_place2d_error_nodes"] = error_nodes
            return "UDIM 贴图连接的 place2dTexture 节点被修改过：\n{}".format("\n".join(error_nodes))


    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """恢复 UDIM place2dTexture 默认参数"""
    try:
        PLACE2D_DEFAULT_ATTRS = {
            "coverageU": 1.0,
            "coverageV": 1.0,
            "translateFrameU": 0.0,
            "translateFrameV": 0.0,
            "rotateFrame": 0.0,
            "mirrorU": 0,
            "mirrorV": 0,
            "wrapU": 1,
            "wrapV": 1,
            "stagger": 0,
            "repeatU": 1.0,
            "repeatV": 1.0,
            "offsetU": 0.0,
            "offsetV": 0.0,
            "rotateUV": 0.0,
            "noiseU": 0.0,
            "noiseV": 0.0,
        }
        def repair():
            error_nodes = process_data.get("udim_place2d_error_nodes",[])

            for node_name in error_nodes:
                node = pm.PyNode(node_name)

                for attr, value in PLACE2D_DEFAULT_ATTRS.items():
                    node.setAttr(attr, value)

                logger.warning("AUTO FIX: 恢复 place2dTexture '{}' 默认参数".format(node_name))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
