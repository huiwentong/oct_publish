# -*- coding: utf-8 -*-
import re,traceback
import maya.cmds as cmds
import maya.utils as utils
from oct.pipeline.task_context import TaskContext

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 Hair_xgenBaseGeo 包裹文件，并清理 Arnold 属性。"""
    try:
        def process():
            task_id = process_data["task_id"]
            tc = TaskContext(task_id) or TaskContext.from_env()
            version_dir = process_data.get("version_dir")
            entity_name = tc.entity_name
            version_dir = str(version_dir).replace("\\","/").rstrip("/")

            cmds.select(clear=1)
            cmds.select("Hair_xgenBaseGeo")
            wrap_file = "{}/{}.wrap.ma".format(version_dir, entity_name)
            cmds.file(wrap_file, force=1, options="vv=0;", typ="mayaAscii", pr=1, es=1)

            # - Remove Arnold Attribute
            with open(wrap_file, "r") as f:
                ma_data = f.read()
            ma_data = re.sub("	setAttr \".ai_translator\" -type \"string\" (.*?);",
                             "",
                             ma_data)
            with open(wrap_file, "w") as f:
                f.write(ma_data)

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()