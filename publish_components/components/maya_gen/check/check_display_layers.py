# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查是否有隐藏的显示层"""
    try:
        hidden_layers = []
        display_layer_list = pm.ls(type='displayLayer')
        for layer in display_layer_list:
            if layer.getAttr('visibility') == 0 and not pm.referenceQuery(layer, isNodeReferenced=1):
                hidden_layers.append(layer.name())

        result = u'以下动画层被隐藏，请显示后确认对画面有无影响， 有影响需要ctrl+h隐藏: \n'
        result += '\n'.join(hidden_layers)
        return result
    except Exception:
        return traceback.format_exc()
