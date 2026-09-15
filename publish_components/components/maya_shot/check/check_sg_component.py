# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils

from oct_maya.tools.lay.usd_lay_manager_new.core import check_scene_comps


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查当前场景资产是否和 SG 记录的 Components 对齐（场景可以多，不能少）
    """
    # 老 lay/check_sg_component。老工具 ani / blk 表单上有“拆分任务”勾选框，
    # lay 没有，这里 is_split_task 固定 False；后续迁 blk / ani 时从 submit_data 里取。
    try:
        task_id = int(process_data['task_id'])
        is_split_task = bool(submit_data.get('is_split_task', False))

        result_text = utils.executeInMainThreadWithResult(
            lambda: check_scene_comps(task_id=task_id, is_split_task=is_split_task))
        if result_text:
            return result_text
    except:
        return traceback.format_exc()
