# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import maya.utils as utils
import xgenm.xgGlobal as xgg

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen Description 是否启用 Arnold Renderer。"""
    try:
        def check():
            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"

            error_msg = ''
            palette = palettes[0]
            descriptions = xg.descriptions(str(palette))
            for _des in descriptions:
                if xg.getActive(str(palette), str(_des), "Renderer") != 'RendermanRenderer':
                    error_msg += u'description "{}" 的Renderer设置不对\n'.format(_des)
                else:
                    if xg.getAttr('renderer', str(palette), str(_des), "RendermanRenderer") != 'Arnold Renderer':
                        error_msg += u'description "{}" 的Renderer不是Arnold Renderer'.format(_des)
            if error_msg:
                return error_msg

            return None

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result

    except Exception:
        return traceback.format_exc()

def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """自动将 XGen Description Renderer 设置为 Arnold Renderer。"""
    try:
        def repair():
            palette = xg.palettes()[0]
            descriptions = xg.descriptions(str(palette))
            for _des in descriptions:
                xg.setActive(str(palette), str(_des), 'RendermanRenderer')
                xg.setAttr('renderer', 'Arnold Renderer', str(palette), str(_des), "RendermanRenderer")
            xgg.DescriptionEditor.refresh('Full')

        utils.executeInMainThreadWithResult(repair)
    except Exception:
        return traceback.format_exc()