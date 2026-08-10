# -*- coding:utf-8 -*-
import traceback
from oct.pipeline import path_acs


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
记录需要建立链接的 无版本号版本和文件
    """
    try:
        src = process_data['version_dir']
        dst = process_data['version_dir_no_num']

        logger.info(str(src))
        logger.info(str(dst))
        path_acs.symlink(src,dst, remove_exists=True)
    except:
        return traceback.format_exc()

