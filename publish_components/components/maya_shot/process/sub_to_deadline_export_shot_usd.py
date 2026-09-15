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
    # 发布项作用：把当前版本目录下的 ma 文件提交到 Deadline 农场，用 maya_cache-2024 环境 (带mtoa会返回错误)
    # 执行 export_shot_usd / export_shot_usd_ani 生成镜头 USD；场景没有 |World 组时跳过。
    # 依赖 gen/create_sg_version 写入的 process_data['sg_version']。
    try:
        export_command = process_data.get('shot_usd_export_command', 'export_shot_usd')
        if export_command not in ('export_shot_usd', 'export_shot_usd_ani'):
            return u'不支持的镜头 USD 导出命令: {0}'.format(export_command)
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

            # 农场统一用 maya_cache-2024 环境导出
            command = 'rez-env maya_cache-2024 oct_maya oct_cache_exporter -- {0} "{1}" {2} {3}'.format(
                export_command, ma_file, tc.task_id, version_id)

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
