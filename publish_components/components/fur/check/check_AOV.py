# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.app.renderSetup.model.renderLayer as renderLayer
import maya.app.renderSetup.model.renderSetup as renderSetup

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查并自动清理 Render Layer 和 Arnold AOV。"""
    try:
        rs=renderSetup.instance()
        layers=rs.getRenderLayers()
        aovs=cmds.ls(type="aiAOV") or []

        if layers or aovs:
            if logger:
                if layers:
                    logger.warning(u"发现 Render Layer：{}".format(", ".join(layer.name() for layer in layers)))
                if aovs:
                    logger.warning(u"发现 Arnold AOV：{}".format(", ".join(aovs)))

            if layers:
                rs.switchToLayerUsingLegacyName("defaultRenderLayer")
                cmds.setAttr("defaultRenderLayer.renderable",0)
                for layer in layers:
                    if logger:
                        logger.warning(u"AUTO FIX: 清理 Render Layer {}".format(layer.name()))
                    rs.detachRenderLayer(layer)
                    renderLayer.delete(layer)

            for aov in aovs:
                if logger:
                    logger.warning(u"AUTO FIX: 清理 AOV {}".format(aov))
                cmds.delete(aov)

    except Exception:
        return traceback.format_exc()