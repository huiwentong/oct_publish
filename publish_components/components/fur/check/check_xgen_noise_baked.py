# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import pymel.core as pm
import maya.utils as utils
import xgenm.xgGlobal as xgg

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen Noise Modifier 是否已烘焙。以保证每次渲染效果一致"""
    try:
        def check():
            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"

            error_msg = ''
            ub_noise = []
            palette = palettes[0]
            descriptions = xg.descriptions(palette)
            for description in descriptions:
                modifiers = xg.fxModules(palette, description)
                for modifier in modifiers:
                    if xg.fxModuleType(palette, description, modifier) == 'NoiseFXModule':
                        if xg.getAttr('mode', palette, description, modifier) == '0':
                            error_msg += u'Description "{}" 中的 "{}" Noise修改器没有烘焙数据\n'.format(description, modifier)
                            ub_noise.append([description, modifier])
            if error_msg:
                return error_msg, ub_noise
            return None, None

        error_msgs, unbaked_noise= utils.executeInMainThreadWithResult(check)
        if error_msgs:
            process_data.update({"xgen_unbaked_noise": unbaked_noise})
            return error_msgs

    except Exception:
        return traceback.format_exc()

def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """烘焙未完成的 XGen Noise Modifier。"""
    try:
        def repair():
            palette = xg.palettes()[0]
            xgen_unbaked_noise = process_data.get("xgen_unbaked_noise", [])
            for _des, _mod in xgen_unbaked_noise:
                xg.setAttr('mode', '2', str(palette), str(_des), str(_mod))
                cmd = 'xgmNullRender -pb "' + _des + '"'
                pm.mel.eval(cmd)
                xg.setAttr('mode', '1', str(palette), str(_des), str(_mod))
            xgg.DescriptionEditor.refresh('Full')

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()