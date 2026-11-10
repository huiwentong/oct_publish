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
            warn = logger.warning if logger is not None else pm.warning
            for layer in pm.ls(type='renderLayer'):
                layer_name = layer.name()
                if layer_name in RENDER_LAYER_WHITELIST:
                    continue
                if layer.isReferenced():
                    warn('跳过引用的 Render Layer: {}'.format(layer_name))
                    continue

                unlocked = False
                try:
                    if pm.lockNode(layer, query=True, lock=True)[0]:
                        pm.lockNode(layer, lock=False)
                        unlocked = True
                    pm.delete(layer)
                except RuntimeError as error:
                    warn('无法删除 Render Layer {}: {}'.format(layer_name, error))
                finally:
                    if unlocked and pm.objExists(layer_name):
                        pm.lockNode(layer, lock=True)
            pm.delete(pm.ls(type='shot'))

        utils.executeInMainThreadWithResult(process)
    except:
        return traceback.format_exc()

