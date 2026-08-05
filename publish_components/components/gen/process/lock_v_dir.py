# -*- coding: utf-8 -*-
import traceback
from oct.pipeline.path_acs import lock_path

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    锁住版本文件
    """

    try:
        publish_root = process_data.get('publish_root')
        lock_path(publish_root)

        version_dir = process_data.get('version_dir')
        lock_path(version_dir, True)
    except:
        return traceback.format_exc()


