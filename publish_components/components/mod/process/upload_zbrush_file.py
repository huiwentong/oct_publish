# -*- coding: utf-8 -*-
import traceback
import os,shutil
from oct.pipeline.path_acs import unlock_path
from oct.pipeline.task_context import TaskContext
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    上传zb文件
    """
    try:
        zbrush_file = submit_data.get("zb_file")
        if zbrush_file and os.path.isfile(zbrush_file):
            v_dir_ma_file = process_data.get("v_dir_ma_file")
            full_zb_v_file = v_dir_ma_file.replace('.ma','.ztl')
            unlock_path(os.path.dirname(full_zb_v_file))
            if os.path.exists(full_zb_v_file):
                unlock_path(full_zb_v_file)
            shutil.copy2(zbrush_file, full_zb_v_file)

    except:
        return traceback.format_exc()


