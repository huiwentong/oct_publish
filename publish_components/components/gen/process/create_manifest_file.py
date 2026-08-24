# -*- coding: utf-8 -*-
import traceback
from oct.pipeline.path_acs import unlock_path, lock_path
from oct.utils.manifest_gen import generate_manifest_json

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    为当前发布版本创建 manifest 文件
    """

    try:
        version_dir = process_data.get("version_dir")
        unlock_path(version_dir)
        generate_manifest_json(version_dir)
        lock_path(version_dir)
    except:
        return traceback.format_exc()


