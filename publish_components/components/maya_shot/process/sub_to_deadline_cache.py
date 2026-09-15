# -*- coding: utf-8 -*-
import subprocess
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    提交当前版本到 Deadline 输出缓存（oct_cache_exporter version_to_deadline）
    """
    # 老 ani/sub_to_deadline：version_to_deadline 自己会往 Deadline 提任务，这里只是起一个本地进程。
    # 依赖 gen/create_sg_version 写入的 process_data['sg_version']。
    try:
        version_id = process_data['sg_version']['id']
        maya_version = utils.executeInMainThreadWithResult(lambda: int(cmds.about(v=True)))
        if maya_version <= 2020:
            cmd = 'rez-env oct_cache_exporter -- version_to_deadline {0}'.format(version_id)
        else:
            cmd = 'rez-env oct_cache_exporter -- version_to_deadline2024 {0}'.format(version_id)
        logger.info(cmd)

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        if result.returncode != 0:
            return u"提交缓存输出任务失败 (exit {0}):\n{1}".format(result.returncode, result.stderr)
    except:
        return traceback.format_exc()
