# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查无用 Set、Layer、AOV、无用材质等节点"""
    try:
        def check():
            LEGAL_SETS = {"defaultLightSet", "defaultObjectSet", "initialParticleSE", "initialShadingGroup"}
            LEGAL_LAYERS = {"defaultLayer", "defaultRenderLayer", "BaseAnimation", "masterLayer"}
            #清理无用的材质节点
            pm.mel.eval('MLdeleteUnused;')

            data = {
                "sets": [
                    n.name()
                    for n in pm.ls(type="objectSet")
                    if n.name() not in LEGAL_SETS and not n.isReferenced() and n.nodeType() == 'objectSet'
                ],
                "layers": [
                    n.name()
                    for n in pm.ls(type=["displayLayer", "renderLayer", "animLayer"])
                    if n.name() not in LEGAL_LAYERS and not n.isReferenced()
                ],
                "aovs": [n.name() for n in pm.ls(type="aiAOV") if not n.isReferenced()
                ]
            }

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        errors = []

        if error_data["sets"]:
            errors.append("需要清理的 Set:\n{}".format("\n".join(error_data["sets"])))

        if error_data["layers"]:
            errors.append("需要清理的 Layer:\n{}".format("\n".join(error_data["layers"])))

        if error_data["aovs"]:
            errors.append("需要清理的 AOV:\n{}".format("\n".join(error_data["aovs"])))

        if errors:
            process_data["scene_cleanup_error_nodes"] = error_data
            return "\n\n".join(errors)

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """清理无用 Set、Layer、AOV 节点"""
    try:
        def repair():
            failed = []
            error_data = process_data.get("scene_cleanup_error_nodes", {})
            for nodes in error_data.values():
                for node in nodes:
                    try:
                        pm.lockNode(node, lock=False)
                        pm.delete(node)
                        logger.warning("AUTO FIX: 删除无用节点 '{}'".format(node))

                    except Exception:
                        failed.append(node)

            return failed

        fail_nodes = utils.executeInMainThreadWithResult(repair)
        if fail_nodes:
            msg = "以下节点无法删除:\n{}".format("\n".join(fail_nodes))
            logger.error(msg)
            return msg

    except Exception:
        return traceback.format_exc()
