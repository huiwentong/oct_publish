# -*- coding: utf-8 -*-
import re,traceback
import xgenm as xg
import maya.cmds as cmds
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen xgVersion 中的 Maya 版本，不正确则自动修复。"""
    try:
        def check():
            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"

            palette = palettes[0]
            xgVersion = cmds.getAttr(palette+'.xgVersion')
            maya_version = cmds.about(version=True)

            if maya_version not in xgVersion:
                return 'xgen属性xgVersion的maya版本错误'
            return None

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result

    except Exception:
        return traceback.format_exc()

def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """自动修复。"""
    try:
        def repair():
            palette = xg.palettes()[0]
            xgVersion = cmds.getAttr(palette + '.xgVersion')
            maya_version = cmds.about(version=True)
            new_xgVersion = re.sub('Maya\d+', 'Maya{}'.format(maya_version), xgVersion)
            cmds.setAttr(palette + '.xgVersion', new_xgVersion, type='string')
            cmds.file(save=1, force=True)

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()