# -*- coding: utf-8 -*-
import traceback
from oct.pipeline.task_context import TaskContext


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    旧的资产名字，不可以提交
    """
    try:
        task_id = process_data.get("task_id")
        tc = TaskContext(task_id) or TaskContext.from_env()
        tc.refresh()
        sg_target_asset = tc.entity.sg_target_asset

        if sg_target_asset:
            return "当前资产为旧资产，新得资产为：{}".format(sg_target_asset.name)


    except:
        return traceback.format_exc()


