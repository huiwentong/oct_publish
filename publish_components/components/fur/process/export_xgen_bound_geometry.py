# -*- coding: utf-8 -*-

import os, traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils


def _process(process_data, logger=None):
    """导出 XGen 生长面和动力学曲线 Alembic 缓存。"""
    version_dir = process_data.get("version_dir")
    bind_geos = process_data.get("xgen_bound_geometry", [])
    if not version_dir:
        return u"没有获取到 version_dir"
    if not bind_geos:
        return u"没有获取到 xgen_bound_geometry"

    abc_root = version_dir.rstrip("/") + "/alembic"
    if not os.path.exists(abc_root):
        os.makedirs(abc_root)

    root_string = "".join(" -root {}".format(path) for path in bind_geos)
    base_file = abc_root + "/base.abc"
    mel.eval(
        'AbcExport -j "-frameRange 1 1 -attrPrefix xgen -stripNamespaces '
        '-uvWrite -worldSpace -writeUVSets{} -file {}";'.format(root_string, base_file)
    )

    curve_shapes = cmds.listRelatives(
        "|Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx",
        ad=True, type="nurbsCurve", f=True
    ) or []

    for shape in curve_shapes:
        if cmds.getAttr(shape + ".intermediateObject"):
            continue
        parents = cmds.listRelatives(shape, parent=True, f=True) or []
        if not parents:
            continue
        curve = parents[0]
        if not cmds.objExists(curve + ".attachedXgenDesc"):
            continue
        desc = cmds.getAttr(curve + ".attachedXgenDesc")
        if not cmds.objExists(shape + ".attachedXgenDesc"):
            cmds.addAttr(shape, ln="attachedXgenDesc", dt="string")
        cmds.setAttr(shape + ".attachedXgenDesc", desc or "", type="string")

    curves = cmds.listRelatives(
        "|Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx", c=True, f=True
    ) or []

    if curves:
        root_string = "".join(" -root {}".format(path) for path in curves)
        curves_file = abc_root + "/curves.abc"
        mel.eval(
            'AbcExport -j "-frameRange 1 1 -attr attachedXgenDesc '
            '-stripNamespaces -worldSpace{} -file {}";'.format(root_string, curves_file)
        )

    if logger:
        logger.info(u"XGen Alembic 导出完成：{}".format(abc_root))
    return ""


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """导出 XGen 生长面和动力学曲线 Alembic 缓存。"""
    try:
        result = utils.executeInMainThreadWithResult(_process, process_data, logger)
        return result or ""
    except Exception:
        return traceback.format_exc()