# -*- coding:utf-8 -*-
import traceback, shutil
from pathlib import Path
from oct.pipeline import path_acs
from oct.pipeline.task_context import TaskContext


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

        elif publish_type.lower() == 'dailies':
            task_id = process_data.get("task_id")
            tc = TaskContext(task_id) or TaskContext.from_env()
            has_publish_v = bool(tc.task.latest_published_version)
            if has_publish_v:
                abc_names = ['camWhole.abc', 'colorpanelsWhole.abc', 'camUpper.abc', 'colorpanelsUpper.abc',
                             'camCloseup.abc', 'colorpanelsCloseup.abc',]
                for abc_name in abc_names:
                    src_abc = Path(src) / "alembic" / abc_name
                    dst_abc = Path(dst) / "alembic" / abc_name
                    back_dir = Path(dst) / "alembic" / "bake_up"
                    bake_abc = Path(back_dir) / abc_name
                    if dst_abc.is_file() and not bake_abc.is_file():
                        if not back_dir.exists():
                            back_dir.mkdir()
                        shutil.move(dst_abc, back_dir / abc_name)
                    shutil.copy2(src_abc, dst_abc)
            else:
                logger.warning("当前资产'{}'没有publish 过版本！ 无法链接abc！".format(tc.entity_name))

        else:
            logger.info(str(src))
            logger.info(str(dst))
            path_acs.symlink(src,dst, remove_exists=True)
    except:
        return traceback.format_exc()

