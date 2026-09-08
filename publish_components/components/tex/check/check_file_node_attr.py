# -*- coding: utf-8 -*-
import os
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Roughness / Bump / Displacement / Metalness 等贴图属性"""
    try:
        def type_match(path):
            SPEC_TYPES = {"roughness", "normal", "disp", "metalness", "dis", "opacity", "subsurfaceweight", "alpha"}
            tokens = os.path.basename(path).lower().replace("_", ".").split(".")
            return any(token in SPEC_TYPES for token in tokens)

        def check():
            data = {}
            for node in pm.ls(type=["file", "aiImage"]):
                path = node.fileTextureName.get() if node.hasAttr("fileTextureName") else node.filename.get()
                if not type_match(path):
                    continue

                attrs = {}
                if node.colorSpace.get() != "Utility - Raw":
                    attrs["colorSpace"] = "Utility - Raw"

                if not node.ignoreColorSpaceFileRules.get():
                    attrs["ignoreColorSpaceFileRules"] = True

                if node.hasAttr("alphaIsLuminance") and not node.alphaIsLuminance.get():
                    attrs["alphaIsLuminance"] = True

                if attrs:
                    data[node.name()] = attrs

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        if error_data:
            process_data["texture_node_attr_error_nodes"] = error_data
            return "部分贴图节点属性错误:\n{}".format(
                "\n".join("{}: {}".format(node, ", ".join(attrs)) for node, attrs in error_data.items()))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复贴图属性"""
    try:
        def repair():
            error_data = process_data.get("texture_raw_attr_error_nodes", {})
            for node_name, attrs in error_data.items():
                node = pm.PyNode(node_name)

                for attr, value in attrs.items():
                    if attr == "colorSpace":
                        node.setAttr(attr, value, type="string")
                    else:
                        node.setAttr(attr, value)
                logger.warning("AUTO FIX: 修复贴图节点 '{}' 属性: {}".format(node_name, ", ".join(attrs)))
        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
