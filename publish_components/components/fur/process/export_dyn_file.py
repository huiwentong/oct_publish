# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds
import maya.utils as utils
from oct.pipeline.task_context import TaskContext

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """删除 XGen Palette 后导出动力学文件。"""
    try:
        def process():
            task_id = process_data["task_id"]
            tc = TaskContext(task_id) or TaskContext.from_env()
            entity_name = tc.entity_name
            version_dir = process_data.get("version_dir")
            cmds.delete(cmds.ls(type="xgmPalette"))
            cmds.select(clear=1)
            cmds.select("Root_grp")
            cmds.file(version_dir + '/{}.dyn.ma'.format(entity_name),
                      force=1,
                      options="vv=0;",
                      typ="mayaAscii",
                      pr=1, es=1)

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()