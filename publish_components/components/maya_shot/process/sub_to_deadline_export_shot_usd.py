# -*- coding: utf-8 -*-
import os
import traceback
from datetime import datetime

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline import deadline
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    提交 Deadline 任务输出镜头文件的 USD（export_shot_usd）
    """
    # 老 proj_mk2_gen/sub_to_deadline_export_shot_usd。改用 oct.pipeline.deadline.CommandLineJob 提交，
    # 与 asb_split/submit_asb_deadline_task 一致。老代码按 deadlinecommand 版本切 pool（10.4 用 cache/user，
    # 否则 alembic），现在农场统一是 10.4，直接用 cache / user。
    # 依赖 gen/create_sg_version 写入的 process_data['sg_version']。
    try:
        if not utils.executeInMainThreadWithResult(lambda: cmds.objExists('|World')):
            logger.info(u"场景没有 |World 组，不提交镜头 USD 输出任务")
        else:
            tc = TaskContext(process_data['task_id'])
            proj_name = tc.project_name.lower()
            version_name = process_data['version_name']
            version_id = process_data['sg_version']['id']
            # export_shot_usd 按 '/' 拆分路径获取项目名，Windows 下也必须保留正斜杠。
            ma_file = '{0}/{1}.ma'.format(process_data['version_dir'], version_name).replace('\\', '/')
            if not os.path.isfile(ma_file):
                return u"版本目录里没有 ma 文件，无法提交 USD 输出: {0}".format(ma_file)

            maya_version = utils.executeInMainThreadWithResult(lambda: int(cmds.about(v=True)))
            if maya_version <= 2020:
                packages = 'maya-2019 maya_usd oct_maya NemoMaya oct_cache_exporter'
            else:
                packages = 'maya_cache-2024 oct_maya oct_cache_exporter'
            command = 'rez-env {0} -- export_shot_usd "{1}" {2} {3}'.format(
                packages, ma_file, tc.task_id, version_id)

            job_name = '{0} [export_shot_usd]'.format(os.path.basename(ma_file))
            logger.info(u"提交任务: {0}".format(job_name))
            logger.info(command)

            job = deadline.CommandLineJob(name=job_name)
            job.set_command(command)
            job.set_priority(priority=100)
            job.set_pool(pool='cache')
            job.set_secondary_pool(pool='user')
            job.set_batch_name('{0} - {1}'.format(proj_name, version_name.rsplit('.', 1)[0]))
            job.set_comment(datetime.now().strftime('%Y%m%d%H%M'))
            job.set_environment({'OCT_USER_DEPARTMENT': 'Animation',
                                 'OCT_USER_DEPARTMENT_SHORT_NAME': 'ani',
                                 'OCT_PROJECT': proj_name})

            job_id = job.submit()
            if not job_id:
                return u'提交 Deadline 任务失败: {0}'.format(job_name)
            logger.info(u"{0} -> deadline job {1}".format(job_name, job_id))
    except:
        return traceback.format_exc()
