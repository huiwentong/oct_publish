# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查生长面是否正确包裹到high组模型下，以继承动态。"""
    try:
        def check():
            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"

            palette = palettes[0]
            lst_boundGeometry = ()
            for description in xg.descriptions(palette):
                lst_boundGeometry += xg.boundGeometry(palette, description)
            lst_boundGeometry = set(lst_boundGeometry)
            res = ""
            for boundGeo in lst_boundGeometry:
                _node = pm.PyNode(boundGeo)
                if not _node.inMesh.isConnected():
                    res += u"生长面 {} 没有设置包裹".format(boundGeo)
            if res:
                return res
            return None

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result

    except Exception:
        return traceback.format_exc()