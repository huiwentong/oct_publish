# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 overrideEnabled"""
    try:
        def check():
            n_geo = process_data.get("geo", "|Root_grp|Geo_grp")
            return [
                str(node)
                for node in pm.listRelatives(n_geo, ad=True)
                if pm.objExists(node + ".overrideEnabled")
                and pm.getAttr(node + ".overrideEnabled")
            ]

        error_nodes = utils.executeInMainThreadWithResult(check)
        if error_nodes:
            process_data["override_enabled_error_nodes"] = error_nodes
            return "以下节点开启了 overrideEnabled:\n{}".format("\n".join(error_nodes))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """关闭 overrideEnabled"""
    try:
        def repair():
            error_nodes = process_data.get("override_enabled_error_nodes", [])
            for node in error_nodes:
                attr = node + ".overrideEnabled"
                pm.setAttr(attr, lock=False)
                pm.setAttr(attr, False)
                logger.warning("AUTO FIX: 关闭节点 '{}' 的 overrideEnabled 属性".format(node))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
