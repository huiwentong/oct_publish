# -*- coding: utf-8 -*-
import os
import traceback

from oct.pipeline import deadline


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    提交子资产发布任务到Deadline
    """
    # 按 gen_asset_data 的顺序逐个提交，ASB 类型的任务依赖它下面所有子资产的任务，
    # 保证子资产先发布完、父 ASB 再做 USD 组装。
    #
    # 依赖 gen_asb_deadline_job 回写的 deadline_job_file。
    try:
        # 农场端执行脚本。这里没有用 __file__ 定位 —— CLI 模式下 main() 会被抽进
        # 临时脚本执行，__file__ 指向的是 %TEMP% 里的文件，算出来的相对路径全是错的。
        #
        # _new 版是新架构版本，跑 publish_components 里的组件，不依赖 publish_tool。
        # 同目录下的 run_asb_deadline_job.py 是老版本，仍在生产使用，不要动它。
        script_path = r'Z:\TD\pipeline\scripts\run_asb_deadline_job_new.py'

        gen_asset_data = process_data["gen_asset_data"]

        jobs = {}  # 资产名 -> deadline job id
        for asset_name, asset_info in gen_asset_data.items():
            sub_asset_type = asset_info['asset_type']
            deadline_job_file = asset_info['deadline_job_file']

            job_name = '[asb_export] {0}.{1}'.format(sub_asset_type, asset_name)
            # rez 环境必须带上 oct_publish —— 农场脚本要 import publish_components
            command = 'rez-env maya-2024 oct_maya oct_publish -- mayapy "{0}" "{1}"'.format(
                script_path, deadline_job_file)
            command = command.replace('/', os.sep)

            logger.info(u"提交任务: {0}".format(job_name))
            logger.info(command)

            job = deadline.CommandLineJob(name=job_name)
            job.set_command(command)
            job.set_job_error_limit(number=3)      # 限制任务失败重试次数
            job.set_priority(priority=70)
            job.set_deny_list(deny_list=['liulu', 'ls'])
            job.set_pool(pool='cache')
            job.set_secondary_pool(pool='user')

            # ASB 要等它下面的子资产都发布完，才能做 USD 组装
            if sub_asset_type == 'ASB':
                dependent_id_list = [jobs[longname.split('|')[-1]]
                                     for longname in asset_info['sub_assets']]
                job.set_dependencies(parents=dependent_id_list)

            job_id = job.submit()
            if not job_id:
                return u'提交Deadline任务失败: {0}\n已提交成功的任务: {1}'.format(job_name, jobs)

            jobs[asset_name] = job_id

        for asset_name, job_id in jobs.items():
            logger.info(u"{0} -> deadline job {1}".format(asset_name, job_id))
        logger.info(u"已提交 {0} 个 Deadline 任务".format(len(jobs)))

    except:
        return traceback.format_exc()
