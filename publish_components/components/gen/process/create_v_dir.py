# -*- coding: utf-8 -*-
import os
import traceback
from publish_core.database.entity import SGEntity
from oct.pipeline.path_acs import old_get_path, unlock_path, make_dirs


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    建立版本文件
    """

    try:
        task_id = process_data.get("task_id")
        project_name = process_data.get("project_name")
        publish_root = process_data.get("publish_root")
        version_dir = process_data.get("version_dir")
        if not project_name:
            task = SGEntity('Task', process_data['task_id'])
            project_name = task.project.name

        if not os.path.exists(publish_root):
            old_get_path(mount_point='publish', show_name=project_name.upper(),
                         entity_type='Task', id=task_id, create=True)
        else:
            unlock_path(publish_root)

        if not os.path.exists(version_dir + "/preview"):
            make_dirs(version_dir + '/preview')
            unlock_path(version_dir + '/preview', True)

        unlock_path(version_dir)
        if not os.path.isdir(version_dir + '/preview'):
            return u'无法创建版本预览文件夹 {}/preview'.format(version_dir)

    except:
        return traceback.format_exc()


