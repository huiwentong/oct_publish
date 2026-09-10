# -*- coding:utf-8 -*-
import traceback, shutil
from pathlib import Path
from oct.pipeline import path_acs


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
记录需要建立链接的 无版本号版本和文件
    """
    try:
        src = process_data['version_dir']
        dst = process_data['version_dir_no_num']
        # TODO 20260910 path_acs 服务器挂载有问题，导致软硬链接失效 暂时先copy， 服务器修复后删除 publish_type 相关即可
        publish_type = process_data.get("publish_type", "")
        if publish_type.lower() == 'submit':
            if not Path(dst).exists():
                path_acs.recursive_mkdirs(dst)
            path_acs.unlock_path(dst, True)
            src_p = Path(src)
            dst_p = Path(dst)
            for child in src_p.iterdir():
                dst_child_p = dst_p / child.name

                if dst_child_p.exists():
                    if dst_child_p.is_dir():
                        shutil.rmtree(dst_child_p)
                    else:
                        dst_child_p.unlink()

                if child.is_dir():
                    shutil.copytree(child, dst_child_p)
                else:
                    shutil.copy2(child, dst_child_p)
        else:
            logger.info(str(src))
            logger.info(str(dst))
            path_acs.symlink(src,dst, remove_exists=True)
    except:
        return traceback.format_exc()

