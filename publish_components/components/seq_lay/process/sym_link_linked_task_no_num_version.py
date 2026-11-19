# -*- coding: utf-8 -*-
import traceback

from oct.pipeline import path_acs


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    建立各镜头的无版本号版本目录，链接到本次版本
    """
    try:
        for shot, info in process_data['linked_task_info'].items():
            path_acs.symlink(info['version_dir'], info['version_dir_no_num'], remove_exists=True)
            logger.info(u'{0}: {1} -> {2}'.format(shot, info['version_dir_no_num'], info['version_dir']))
    except:
        return traceback.format_exc()
