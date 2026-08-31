# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 transform 输入连接、锁定及隐藏属性"""
    try:
        def check():
            data = {}
            root = process_data.get("root", "|Root_grp")
            TR_ATTRS = [
                "translateX", "translateY", "translateZ",
                "rotateX", "rotateY", "rotateZ",
                "scaleX", "scaleY", "scaleZ",
                "visibility"
            ]

            for node in pm.listRelatives(root, ad=True, type="transform"):
                if node.type() == "instancer":
                    continue

                connections = [
                    (str(pair[1]), str(pair[0]))
                    for pair in pm.listConnections(node, s=True, d=False, c=True, plugs=True)
                ]

                attrs = [
                    attr for attr in TR_ATTRS
                    if (
                        not pm.getAttr("{}.{}".format(node, attr), keyable=True)
                        or pm.getAttr("{}.{}".format(node, attr), lock=True)
                    )
                ]

                if connections or attrs:
                    data[str(node)] = {
                        "connections": connections,
                        "attrs": attrs
                    }

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        if error_data:
            process_data["transform_attr_error_nodes"] = error_data
            return "以下节点存在输入连接或锁定隐藏属性:\n{}".format("\n".join(error_data))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        error_data = process_data.get("transform_attr_error_nodes", {})

        def repair():
            for node, data in error_data.items():
                for src, dst in data["connections"]:
                    pm.disconnectAttr(src, dst)

                for attr in data["attrs"]:
                    plug = "{}.{}".format(node, attr)
                    pm.setAttr(plug, lock=False)
                    pm.setAttr(plug, keyable=True)

                logger.warning("AUTO FIX: 断开链接并显示解锁节点 '{}'".format(node))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
