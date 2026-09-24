# -*- coding: utf-8 -*-
import re,traceback
import xgenm as xg
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen 生长面命名是否符合 '对应名称_Hair_Face' 的规范。"""
    try:
        def check():
            error_list = []
            palette = xg.palettes()[0]
            lst_boundGeometry = ()
            for description in xg.descriptions(palette):
                lst_boundGeometry += xg.boundGeometry(palette, description)
            lst_boundGeometry = set(lst_boundGeometry)
            for boundGeo in lst_boundGeometry:
                if not re.match('(.*)_Hair_Face', boundGeo):
                    error_list.append(u"生长面命名不规范:{}, 应该为对应名称_Hair_Face".format(boundGeo))
            return error_list

        errors = utils.executeInMainThreadWithResult(check)
        if errors:
            return '\n'.join(errors)

    except Exception:
        return traceback.format_exc()