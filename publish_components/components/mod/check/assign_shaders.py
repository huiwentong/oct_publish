# -*- coding: utf-8 -*-

import traceback
import pymel.core as pm
import maya.utils as utils
import maya.api.OpenMaya as om


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查无材质或使用 initialShadingGroup 的 Face"""
    try:
        def check():
            data = {}
            n_high = process_data.get("root", "|Root_grp|Geo_grp|high")

            for mesh in pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True):
                if "proxyShape" in mesh.nodeName():
                    continue
                sel = om.MSelectionList()
                sel.add(mesh.longName())
                dag = sel.getDagPath(0)
                fn = om.MFnMesh(dag)

                shaders, indices = fn.getConnectedShaders(dag.instanceNumber())
                shader_names = [om.MFnDependencyNode(obj).name() for obj in shaders]
                initial_index = shader_names.index("initialShadingGroup") if "initialShadingGroup" in shader_names else -2
                bad_faces = [i for i, shader_index in enumerate(indices) if shader_index in (-1, initial_index)]

                if bad_faces:
                    data[mesh.longName()] = bad_faces

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        process_data["material_missing_error_nodes"] = error_data

        if error_data:
            return "以下模型存在无材质或 initialShadingGroup Face:\n{}".format(
                "\n".join("{}: {} faces".format(mesh, len(ids)) for mesh, ids in error_data.items()))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复无材质或 initialShadingGroup Face"""
    try:
        def repair():
            shader_name = "default_fix_MAT"
            sg_name = "default_fix_MATSG"
            error_data = process_data.get("material_missing_error_nodes", {})

            shader = pm.PyNode(shader_name) if pm.objExists(shader_name) else pm.shadingNode("lambert", asShader=True, name=shader_name)
            fix_sg = pm.PyNode(sg_name) if pm.objExists(sg_name) else pm.sets(empty=True, renderable=True, noSurfaceShader=True, name=sg_name)
            pm.connectAttr(shader.outColor, fix_sg.surfaceShader, force=True)

            for mesh, ids in error_data.items():
                target = ["{}.f[{}]".format(mesh, i) for i in ids]
                pm.sets(fix_sg, e=True, forceElement=target)
                logger.warning("AUTO FIX: 修复 '{}' {} 个无材质或 initialShadingGroup Face".format(mesh, len(ids)))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
