# -*- coding: utf-8 -*-
import traceback, os
import maya.cmds as cmds
import maya.utils as utils
import xgenm as xg
from publish_components.utils.gen_func import is_outsourcing
from publish_components.utils.maya_utils.maya_path_relinker import execute_relinker

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """后台运行时：设置工程路径并重开 maya 文件"""
    try:
        def open_scene():
            work_file = submit_data.get('ma_file', '')
            if is_outsourcing(work_file):
                execute_relinker(work_file, os.path.dirname(work_file))
            new_workspace = os.path.dirname(work_file).replace('\\', '/')
            cmds.workspace(new_workspace, openWorkspace=True)
            cmds.file(work_file, open=True, force=True)

        if not parent_widget:
            utils.executeInMainThreadWithResult(open_scene)
    except Exception:
        return traceback.format_exc()