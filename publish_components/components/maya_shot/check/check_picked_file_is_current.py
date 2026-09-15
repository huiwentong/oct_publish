# -*- coding: utf-8 -*-
import os
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查表单里选取的 Maya 文件就是当前打开的场景
    """
    # 发布表单里选的工程文件必须是当前打开的场景，
    # 否则后面的检查全是针对当前场景做的，拷进版本目录的却是另一个文件。
    try:
        def check():
            return cmds.file(query=True, sceneName=True) or ''

        scene_path = utils.executeInMainThreadWithResult(check).replace('\\', '/')
        picked_path = (submit_data.get('ma_file') or '').replace('\\', '/')
        if not scene_path:
            return u"当前 Maya 没有打开任何场景文件，请先保存工程文件"
        if os.path.normcase(scene_path) != os.path.normcase(picked_path):
            return u"表单里选取提交的 Maya 文件不是当前打开的场景：\n{0}\n当前场景：\n{1}\n请点击 Fix 自动修正".format(
                picked_path, scene_path)
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """把当前打开的场景路径写回表单"""
    try:
        scene_path = utils.executeInMainThreadWithResult(
            lambda: cmds.file(query=True, sceneName=True) or '')
        if not scene_path:
            return u"当前 Maya 没有打开任何场景文件，无法修正"
        submit_data['ma_file'] = scene_path
        process_data['dcc_file'] = scene_path
        logger.info(u"AUTO FIX: 表单工程文件改为当前场景 {0}".format(scene_path))
    except:
        return traceback.format_exc()
