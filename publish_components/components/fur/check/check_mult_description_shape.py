# -*- coding: utf-8 -*-
import traceback
import xgenm as xg
import maya.cmds as cmds
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查每个 XGen Description 下不能存在多个 Transform。"""
    try:
        def check():
            palettes = xg.palettes()
            if len(palettes) != 1:
                return u"xgen palette数量不是一个， 请检查"

            wrong_des = []
            dess = xg.descriptions(palettes[0])
            for des in dess:
                cmds.setAttr(des + '.v', 1)
                trans = cmds.listRelatives(des, c=1, type='transform')
                if len(trans) > 1:
                    wrong_des.append(des)

            if wrong_des:
                return u"发现有多个transform在同一个description的情况：{}".format("\n".join(wrong_des))
            return None

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result

    except Exception:
        return traceback.format_exc()