# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 eyeShell 材质 Specular IOR"""
    try:
        def check():
            bad_mats = set()
            for mesh in pm.ls("eyeshell_*", type="mesh"):
                for sg in pm.listConnections(mesh, type="shadingEngine") or []:
                    for mat in pm.listConnections(sg, type="aiStandardSurface") or []:
                        if mat.specularIOR.get() != 1.0:
                            bad_mats.add(mat.name())

            return sorted(bad_mats)

        error_nodes = utils.executeInMainThreadWithResult(check)
        if error_nodes:
            process_data["eyeshell_specular_error_nodes"] = error_nodes
            return ("眼睛玻璃体反射属性检查，如果IOR是启用，则开启Coat,"
                    "以下 eyeShell 材质的 specularIOR 不是 1.0:\n{}").format("\n".join(error_nodes))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复 eyeShell 材质 Specular IOR 和 Coat"""
    try:
        def repair():
            error_nodes = process_data.get("eyeshell_specular_error_nodes", [])
            for mat_name in error_nodes:
                mat = pm.PyNode(mat_name)
                mat.specularIOR.set(1.0)
                mat.coat.set(1.0)

                logger.warning("AUTO FIX: 设置 '{}' specularIOR=1.0, coat=1.0".format(mat_name))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
