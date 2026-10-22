# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.maya_utils import dialogs

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 high 组下隐藏的几何体"""
    try:
        def check():
            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")

            return [
                node.longName()
                for node in pm.listRelatives(n_high, ad=True, type=("mesh", "transform"), fullPath=True)
                if not node.visibility.get()
            ]

        error_nodes = utils.executeInMainThreadWithResult(check)

        if error_nodes:
            process_data["visibility_error_nodes"] = error_nodes
            message = "以下节点被隐藏，请自行判断是否修复。如果这些是允许的，请‘跳过检查’。:\n{}".format("\n".join(error_nodes))
            if parent_widget:
                selected = dialogs.message_dialog("提示", message, ["跳过检查", "停止提交"], parent=parent_widget)
                if selected == "停止提交":
                    return message
            else:
                return message

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """显示 high 组下隐藏的几何体"""
    try:
        def repair():
            error_nodes = process_data.get("visibility_error_nodes", [])
            for node in error_nodes:
                attr = pm.PyNode(node).visibility
                attr.set(lock=False)
                attr.set(True)
                logger.warning("AUTO FIX: 自动修复节点 '{}' 的 visibility 为 1".format(node))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
