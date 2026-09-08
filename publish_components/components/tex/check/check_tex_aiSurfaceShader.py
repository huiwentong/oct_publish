# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 high 下模型是否使用 Maya 材质，而非 Arnold 材质"""
    try:
        def check():
            MAYA_SHADER_TYPES = {"blinn", "lambert", "phong", "anisotropic"}
            n_high = process_data.get("high", '|Root_grp|Geo_grp|high')
            shading_groups = []
            for shape in pm.listRelatives(n_high, ad=True, type="mesh", fullPath=True):
                shading_groups.extend(pm.listConnections(shape, type="shadingEngine") or [])
            shading_groups = list(set(shading_groups))

            bad_shaders = set()
            for sg in shading_groups:
                if sg == "initialShadingGroup":
                    continue

                shaders = pm.listConnections("{}.aiSurfaceShader".format(sg), source=True, destination=False)
                if not shaders:
                    shaders = pm.listConnections("{}.surfaceShader".format(sg), source=True, destination=False)

                if shaders and pm.nodeType(shaders[0]) in MAYA_SHADER_TYPES:
                    bad_shaders.add(shaders[0])

            return bad_shaders

        error_nodes = utils.executeInMainThreadWithResult(check)
        if error_nodes:
            return "high 组下的模型使用了以下 Maya 材质，而非 Arnold 材质：\n{}".format("\n".join(error_nodes))

    except Exception:
        return traceback.format_exc()
