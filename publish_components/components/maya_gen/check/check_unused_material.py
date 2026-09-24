# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.sg_helper import get_asset_kind, UE_SCENE_TAG


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查未使用的材质"""
    try:
        def check():
            shading_engines = pm.ls(type="shadingEngine")
            used_materials = {
                node
                for sg in shading_engines
                for node in (pm.listConnections(sg, s=True, d=False) or [])
            }

            # standardSurface1 / lambert1 是 Maya 默认材质，没接东西也正常，而且删不掉
            return [
                mat.name() for mat in pm.ls(mat=True)
                if mat not in used_materials
                and mat.nodeName() not in ('standardSurface1', 'lambert1')
            ]

        # UE 场景资产（含没打标签的 ASB）不做这项检查
        if get_asset_kind(process_data.get('task_id')) != UE_SCENE_TAG:
            error_nodes = utils.executeInMainThreadWithResult(check)
            if error_nodes:
                process_data["unused_material_error_nodes"] = error_nodes
                return "以下材质未被使用:\n{}".format("\n".join(error_nodes))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """删除未使用的材质"""
    try:
        error_nodes = process_data.get("unused_material_error_nodes", [])
        def repair():
            for node in error_nodes:
                pm.delete(node)
                logger.warning("AUTO FIX: 删除未使用的材质节点 '{}'".format(node))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
