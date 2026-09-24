# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 Wrap 节点 driverPoints 输入，outMesh 自动改为 worldMesh。"""
    try:
        def check():
            error_msg = ''
            for wrapNode in pm.ls(type="wrap"):
                for dst, _attr in pm.listConnections(wrapNode+".driverPoints", scn=1, p=1, c=1):
                    if _attr.plugNode().type()=="mesh":
                        if _attr.name().endswith(".outMesh"):
                            error_msg += u"包裹节点： {} 的driver输入不符合规范，应该是worldMesh\n".format(str(dst))
            if error_msg:
                return error_msg
            return None

        errors = utils.executeInMainThreadWithResult(check)
        if errors:
            return errors

    except Exception:
        return traceback.format_exc()

def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """outMesh 自动改为 worldMesh。"""
    try:
        def repair():
            for wrapNode in pm.ls(type="wrap"):
                for dst, _attr in pm.listConnections(wrapNode + ".driverPoints", scn=1, p=1, c=1):
                    if _attr.plugNode().type() == "mesh":
                        if _attr.name().endswith(".outMesh"):
                            dst.disconnect()
                            pm.connectAttr(_attr.plugNode().worldMesh, dst)

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()