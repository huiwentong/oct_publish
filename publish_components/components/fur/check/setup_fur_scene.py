# -*- coding: utf-8 -*-
import traceback, os
import maya.cmds as cmds
import maya.utils as utils
import xgenm as xg

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """后台运行时：设置工程路径并重开 maya 文件"""
    try:
        def open_scene():
            work_file = submit_data.get('ma_file', '')
            new_workspace = os.path.dirname(work_file).replace('\\', '/')
            cmds.workspace(new_workspace, openWorkspace=True)
            cmds.file(work_file, open=True, force=True)

        if not parent_widget:
            utils.executeInMainThreadWithResult(open_scene)
    except Exception:
        return traceback.format_exc()