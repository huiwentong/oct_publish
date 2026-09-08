# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 aiSubdivIterations 是否超过 5"""
    try:
        def check():
            high_node = process_data.get("high", "|Root_grp|Geo_grp|high")
            return [
                mesh.longName()
                for mesh in pm.listRelatives(high_node, ad=True, type="mesh", fullPath=True)
                if pm.objExists(mesh + ".aiSubdivIterations")
                and pm.getAttr(mesh + ".aiSubdivIterations") > 5
            ]

        error_nodes = utils.executeInMainThreadWithResult(check)
        if error_nodes:
            process_data["subdiv_iterations_error_nodes"] = error_nodes
            return "以下模型 aiSubdivIterations 超过 5:\n{}".format("\n".join(error_nodes))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复 aiSubdivIterations 为 5"""
    try:
        def repair():
            error_nodes = process_data.get("subdiv_iterations_error_nodes", [])
            for mesh in error_nodes:
                pm.setAttr(mesh + ".aiSubdivIterations", 5)
                logger.warning("AUTO FIX: 设置节点 '{}' 的 aiSubdivIterations 为 5".format(mesh))
        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
