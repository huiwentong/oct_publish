# -*- coding: utf-8 -*-
import re
import traceback
import xgenm as xg
import maya.utils as utils
from oct.pipeline.task_context import TaskContext

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查xgen collection数量和命名"""
    #"Collection有且仅有一个（对应仅一个.xgen文件），并且名字为资产名_任务名。Description 命名：部位_细节名称_Hair 例：Head_Eyebrows_Hair"
    try:
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        task_name = tc.task_name
        entity_name = tc.entity_name

        def check():
            error_msg = ""
            palette_num = len(xg.palettes())
            if palette_num != 1:
                error_msg = u"xgen palette数量不是一个， 请检查"

            palette = xg.palettes()[0]
            if palette != entity_name + '_' + task_name:
                error_msg =  u'xgen palette名字不是当前资产名_任务名：{}_{}'.format(entity_name, task_name)

            for description in xg.descriptions():
                if not re.match('(.*)_(.*)_Hair', description):
                    error_msg += u'xgen description名字不符合规范：部位_细节名称_Hair   {}\n'.format(description)

            return error_msg

        error = utils.executeInMainThreadWithResult(check)
        if error:
            return error
    except Exception:
        return traceback.format_exc()