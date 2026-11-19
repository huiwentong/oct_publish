# -*- coding: utf-8 -*-
import traceback

from oct.pipeline.path_acs import lock_path


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    锁住各镜头的版本文件
    """
    # Deadline 的 lay_seq_output_shot_2024 写入前会自己解锁版本目录，写完再锁。
    try:
        for shot, info in process_data['linked_task_info'].items():
            lock_path(info['publish_root'])
            lock_path(info['version_dir'], True)
    except:
        return traceback.format_exc()
