# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 shader 的 Transmit AOV"""
    #如果 mesh 的 Arnold > Opaque被取消勾选, 对应shader的 Transmit AOV 不能勾选
    try:
        def is_eyes_shader(mt):
            for sg in cmds.listConnections(mt, type="shadingEngine") or []:
                for member in cmds.sets(sg, q=True) or []:
                    node = member.split(".")[0]
                    if cmds.nodeType(node) != "transform":
                        parent = cmds.listRelatives(node, p=True, fullPath=False)
                        if parent:
                            node = parent[0]

                    if "eyeshell" in node.lower():
                        return True

            return False

        def check():
            data = {}

            for mat in cmds.ls(mat=True):
                if (
                    cmds.objExists(mat + ".transmission")
                    and cmds.objExists(mat + ".transmitAovs")
                    and cmds.getAttr(mat + ".transmission") > 0
                ):
                    target = 1 if is_eyes_shader(mat) else 0

                    if cmds.getAttr(mat + ".transmitAovs") != target:
                        data[mat] = target

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        if error_data:
            process_data["shader_transmission_error_nodes"] = error_data
            return ("如果 mesh 的 Arnold > Opaque被取消勾选, 对应shader的 Transmit AOV 不能勾选,"
                    "以下 Shader 的 Transmit AOVs 设置不正确:\n{}").format(
                "\n".join("{} -> {}".format(mat, value) for mat, value in error_data.items())
            )

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复 shader 的 Transmit AOV"""
    try:
        def repair():
            error_data = process_data.get("shader_transmission_error_nodes", {})
            for mat, value in error_data.items():
                cmds.setAttr(mat + ".transmitAovs", value)
                logger.warning("AUTO FIX: 设置 '{}' 的 transmitAovs 为 {}".format(mat, value))
        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
