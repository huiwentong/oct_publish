# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 hairPhysicalShader 材质，并自动替换为 aiStandardHair。"""
    try:
        shader_nodes = utils.executeInMainThreadWithResult(lambda : pm.ls(type='hairPhysicalShader'))
        if shader_nodes:
            return u"存在 hairPhysicalShader 类型材质球：{}".format(
                ", ".join(shader.name() for shader in shader_nodes)
            )

    except Exception:
        return traceback.format_exc()


def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """自动替换为 aiStandardHair。"""
    try:
        def repair():
            for hp_node in pm.ls(type='hairPhysicalShader') or []:
                color = hp_node.rootColorD.get()
                sg = [s for s in hp_node.outputs() if s.nodeType() == 'shadingEngine'][0]
                hp_node.outColor.disconnect(sg.surfaceShader)
                pm.delete(hp_node)
                n_node = pm.shadingNode('aiStandardHair', asShader=True)
                n_node.baseColor.set(color)
                n_node.outColor.connect(sg.surfaceShader)
                logger.warning(u"AUTO FIX: {} 替换为 aiStandardHair".format(hp_node.name()))
        utils.executeInMainThreadWithResult(repair)
    except Exception:
        return traceback.format_exc()