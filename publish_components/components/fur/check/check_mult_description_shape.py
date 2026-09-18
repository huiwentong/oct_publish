# -*- coding: utf-8 -*-

import traceback
import maya.cmds as cmds
import maya.mel as mel


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查每个 XGen Description 下不能存在多个 Transform。"""
    try:
        descriptions = _get_descriptions()
        if not descriptions:
            return u"没有找到 XGen Description"

        wrong_des = []

        for description in descriptions:
            transforms = cmds.listRelatives(description, children=True, type='transform', fullPath=True) or []

            if len(transforms) > 1:
                wrong_des.append(u"{}：{}".format(description, ', '.join(transforms)))

        if wrong_des:
            return u"发现同一个 XGen Description 下存在多个 Transform：\n{}".format('\n'.join(wrong_des))
        return ""

    except Exception:
        return traceback.format_exc()


def _get_descriptions():
    """获取场景中的 XGen Description 节点。"""
    descriptions = mel.eval('ls -long -type "xgmDescription";') or []

    if isinstance(descriptions, str):
        descriptions = [descriptions]

    return descriptions