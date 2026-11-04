# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查是否有多余的动画层"""
    try:
        def process():
            """在 Maya 主线程查询显示层，只返回名称字符串。"""
            anim_layer_list = [layer.name() for layer in pm.ls(type='animLayer')]
            result = [l for l in anim_layer_list if l != 'BaseAnimation']

            return result

        error_layers = utils.executeInMainThreadWithResult(process)

        if error_layers:
            return u'存在以下多余的动画层: {}'.format(", ".join(error_layers))

    except Exception:
        return traceback.format_exc()
