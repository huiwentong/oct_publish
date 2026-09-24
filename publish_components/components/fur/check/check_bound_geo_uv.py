# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen 生长面的 UV 是否全部位于 0-1 第一象限。"""
    try:
        def check():
            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"

            error_msg = ""
            palette = xg.palettes()[0]
            lst_boundGeometry = ()
            for description in xg.descriptions(palette):
                lst_boundGeometry += xg.boundGeometry(palette, description)
            lst_boundGeometry = set(lst_boundGeometry)
            for boundGeo in lst_boundGeometry:
                node = pm.PyNode(boundGeo).getShape()
                u, v = node.getUVs()
                if max(u) > 1 or max(v) > 1 or min(u) < 0 or min(v) < 0:
                    error_msg += u"生长模型: {} 的uv超出第一象限 \n".format(boundGeo)
            if error_msg:
                return error_msg
            return None

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result

    except Exception:
        return traceback.format_exc()