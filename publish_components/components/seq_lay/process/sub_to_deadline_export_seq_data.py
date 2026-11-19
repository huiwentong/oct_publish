# -*- coding: utf-8 -*-
import traceback
from datetime import datetime

from oct.pipeline import deadline


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    提交 Deadline：整场 fbx 导出，以及每个镜头一个拆分任务（生成镜头文件、SG 版本、缓存和镜头 USD）
    """
    # 镜头任务由 oct_cache_exporter/lay_seq_output_shot_2024.py 执行，
    # 参数：镜头名、场次 ma、write_shot_job_info 写的 seq_lay_shots.json（脚本按镜头名取自己那一项）。
    try:
        proj_name = process_data['project_name'].lower()
        ma_file = process_data['v_dir_ma_file'].replace('\\', '/')
        json_file = process_data['shot_job_info_file']

        def submit(job_name, batch_name, command):
            job = deadline.CommandLineJob(name=job_name)
            job.set_command(command)
            job.set_priority(priority=100)
            job.set_pool(pool='cache')
            job.set_secondary_pool(pool='cache')
            job.set_batch_name(batch_name)
            job.set_comment(datetime.now().strftime('%Y%m%d%H%M'))
            job.set_environment({'OCT_USER_DEPARTMENT': 'Animation',
                                 'OCT_USER_DEPARTMENT_SHORT_NAME': 'ani',
                                 'OCT_PROJECT': proj_name})
            logger.info(command)
            job_id = job.submit()
            if not job_id:
                raise RuntimeError(u'提交 Deadline 任务失败: {0}'.format(job_name))
            logger.info(u'{0} -> deadline job {1}'.format(job_name, job_id))

        submit('{0} [export_seq_fbx]'.format(process_data['version_name']),
               '{0}_export_seq_fbx'.format(proj_name),
               'rez-env maya_cache-2024 oct_maya oct_cache_exporter -- lay_seq_export_fbx "{0}"'.format(ma_file))

        for shot, info in process_data['linked_task_info'].items():
            submit('{0}.ma [build shot file]'.format(info['version_name']),
                   '{0} - {1}'.format(proj_name, info['version_name'].rsplit('.', 1)[0]),
                   'rez-env maya_cache-2024 oct_maya oct_cache_exporter -- lay_seq_output_shot_2024 "{0}" "{1}" "{2}"'.format(
                       shot, ma_file, json_file))
    except:
        return traceback.format_exc()
