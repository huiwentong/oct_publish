# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查生长面历史毛发生长模型和组应该位移信息清零"""
    try:
        def check():
            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"

            error_msg = ''
            palette = palettes[0]
            lst_boundGeometry = ()
            for description in xg.descriptions(palette):
                lst_boundGeometry += xg.boundGeometry(palette, description)
            lst_boundGeometry = set(lst_boundGeometry)
            for boundGeo in lst_boundGeometry:
                _node = pm.PyNode(boundGeo)
                _trans = _node.translate.get()
                if _trans[0] != 0 or _trans[1] != 0 or _trans[2] != 0:
                    error_msg += u"生长面{}位移不为0, 请检查\n".format(boundGeo)
                _rot = _node.rotate.get()
                if _rot[0] != 0 or _rot[1] != 0 or _rot[2] != 0:
                    error_msg += u"生长面{}旋转不为0, 请检查\n".format(boundGeo)
                _scale = _node.scale.get()
                if _scale[0] != 1 or _scale[1] != 1 or _scale[2] != 1:
                    error_msg += u"生长面{}缩放不为1, 请检查\n".format(boundGeo)

            _grp = pm.PyNode('Hair_xgenBaseGeo')
            _trans = _grp.translate.get()
            if _trans[0] != 0 or _trans[1] != 0 or _trans[2] != 0:
                error_msg += u"Hair_xgenBaseGeo组位移不为0, 请检查\n"
            _rot = _grp.rotate.get()
            if _rot[0] != 0 or _rot[1] != 0 or _rot[2] != 0:
                error_msg += u"Hair_xgenBaseGeo组旋转不为0, 请检查"
            _scale = _grp.scale.get()
            if _scale[0] != 1 or _scale[1] != 1 or _scale[2] != 1:
                error_msg += u"Hair_xgenBaseGeo组缩放不为1, 请检查"
            return None

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result

    except Exception:
        return traceback.format_exc()