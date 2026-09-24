# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.utils as utils
import maya.app.renderSetup.model.renderLayer as renderLayer
import maya.app.renderSetup.model.renderSetup as renderSetup

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查并清理 Render Layer 和 Arnold AOV。"""
    try:
        def check():
            rs = renderSetup.instance()
            return rs.getRenderLayers() or [], cmds.ls(type="aiAOV") or []

        layers, aovs = utils.executeInMainThreadWithResult(check)
        error_msg = ''
        if layers:
            error_msg += u"发现 Render Layer：{}".format(", ".join(layer.name() for layer in layers))
        if aovs:
            error_msg += u"发现 Arnold AOV：{}".format(", ".join(aovs))

        if error_msg:
            return error_msg

    except Exception:
        return traceback.format_exc()
    
def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查并清理 Render Layer 和 Arnold AOV。"""
    try:
        def repair():
            rs = renderSetup.instance()
            layers = rs.getRenderLayers()
            aovs = cmds.ls(type="aiAOV") or []

            if layers:
                rs.switchToLayerUsingLegacyName("defaultRenderLayer")
                cmds.setAttr("defaultRenderLayer.renderable", 0)
                for layer in layers:
                    logger.warning(u"AUTO FIX: 清理 Render Layer {}".format(layer.name()))
                    rs.detachRenderLayer(layer)
                    renderLayer.delete(layer)

            for aov in aovs:
                logger.warning(u"AUTO FIX: 清理 AOV {}".format(aov))
                cmds.delete(aov)
            utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()