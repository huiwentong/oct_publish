# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """xgen中所有贴图引用必须在description路径下，不可填绝对路径"""
    try:
        def check():
            error_list = []
            palette = xg.palettes()[0]
            for des in xg.descriptions(palette):
                for obj in xg.objects(palette, des):
                    for attr in xg.attrs(palette, des, obj):
                        _value = xg.getAttr(attr, palette, des, obj)
                        if _value:
                            if ':/' in _value.replace('\\', '/'):
                                error_list.append(u"{}-{}-{}的{}属性引用了绝对路径: {}".format(palette, des, obj, attr, _value))
            return error_list

        errors = utils.executeInMainThreadWithResult(check)
        if errors:
            return '\n'.join(errors)

    except Exception:
        return traceback.format_exc()