# -*- coding: utf-8 -*-
import os
import traceback

from oct.pipeline.path_acs import make_dirs, old_get_path, unlock_path


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    建立各镜头 rough_layout 任务的版本文件夹
    """
    # 版本目录已存在的情况 check_shot_versions 已经拦下，这里只管建。
    try:
        for shot, info in process_data['linked_task_info'].items():
            if os.path.exists(info['publish_root']):
                unlock_path(info['publish_root'])
            else:
                old_get_path(mount_point='publish', show_name=process_data['project_name'],
                             entity_type='Task', id=info['task_id'], create=True)
            # 和 gen/create_v_dir 一致：preview 要单独解锁，只对 version_dir 递归解锁时 preview 仍不可写
            make_dirs(info['version_dir'] + '/preview')
            unlock_path(info['version_dir'] + '/preview', True)
            unlock_path(info['version_dir'])
            logger.info(u'{0}: {1}'.format(shot, info['version_dir']))
    except:
        return traceback.format_exc()
