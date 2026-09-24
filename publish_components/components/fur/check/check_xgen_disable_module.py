# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen Modifier 是否处于启用状态。"""
    try:
        def check():
            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"

            error_msg = ''
            palette = palettes[0]
            descriptions = xg.descriptions(str(palette))
            for _des in descriptions:
                for _mod in xg.fxModules(str(palette), str(_des)):
                    if xg.getAttr('active', str(palette), str(_des), str(_mod)) == 'false':
                        error_msg += u'"{}"-"{}"修改器未启用，如不需要请删除 \n'.format(_des, _mod)
            if error_msg:
                return error_msg
            return None

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result

    except Exception:
        return traceback.format_exc()