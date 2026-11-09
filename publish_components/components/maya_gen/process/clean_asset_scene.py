# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

RENDER_LAYER_WHITELIST = ['defaultRenderLayer', 'masterLayer', 'clear_render_layer']

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    清理资产文件中的displayLayer, animationLayer, renderLayer, arnold节点等
    """
    try:
        def process():
            pm.delete(pm.ls(type='displayLayer'))
            pm.delete(pm.ls(type='animLayer'))
            render_layers_to_delete = [
                layer for layer in pm.ls(type='renderLayer')
                if layer.name() not in RENDER_LAYER_WHITELIST
            ]
            if render_layers_to_delete:
                pm.delete(render_layers_to_delete)
            pm.delete(pm.ls(type='shot'))

        utils.executeInMainThreadWithResult(process)
    except:
        return traceback.format_exc()

