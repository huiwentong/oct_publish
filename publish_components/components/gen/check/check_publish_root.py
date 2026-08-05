# -*- coding: utf-8 -*-
import traceback
from oct.pipeline.path_acs import old_get_path
from publish_core.database.entity import SGEntity

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查版本目录文件夹是否存在，不存在自动创建
    """

    try:
        task_id = process_data.get("task_id")
        task = SGEntity('Task', process_data['task_id'])
        old_get_path(mount_point='publish',
                     show_name=task.project.name.upper(),
                     entity_type='Task',
                     id=task_id,
                     create=True)
    except:
        return traceback.format_exc()


