# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 mesh 渲染属性"""
    try:

        def check():
            CHECK_DICT = {
                "castsShadows": 1,
                "receiveShadows": 1,
                "holdOut": 0,
                "motionBlur": 1,
                "primaryVisibility": 1,
                "smoothShading": 1,
                "visibleInReflections": 1,
                "visibleInRefractions": 1,
                "doubleSided": 1,
                "geometryAntialiasingOverride": 0,
                "shadingSamplesOverride": 0,
            }
            data = {}
            n_root = process_data.get("root", "|Root_grp")

            for mesh in pm.listRelatives( n_root, ad=True, type="mesh", ni=True, fullPath=True):
                attrs = {
                    attr: value
                    for attr, value in CHECK_DICT.items()
                    if mesh.getAttr(attr) != value
                }

                if attrs:
                    data[mesh.longName()] = attrs

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        if error_data:
            process_data["mesh_render_attr_error_nodes"] = error_data
            return "以下 Mesh 渲染属性不正确:\n{}".format("\n".join(error_data))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复 mesh 渲染属性"""
    try:
        error_data = process_data.get("mesh_render_attr_error_nodes", {})

        def repair():
            for mesh, attrs in error_data.items():
                node = pm.PyNode(mesh)
                for attr, value in attrs.items():
                    node.setAttr(attr, value)
                    logger.warning("AUTO FIX: 修复节点 '{}' 的 '{}' 属性为 {}".format(mesh, attr, value))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
