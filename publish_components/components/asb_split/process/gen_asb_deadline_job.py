# -*- coding: utf-8 -*-
import json
import os
import traceback

import maya.utils as utils

from oct.pipeline.task_context import TaskContext

from publish_components.utils.maya_utils import get_asb_nodes


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    生成Deadline任务信息，存入json文件
    """
    # 为每个子资产写一个 {asset_type}.{asset_name}.deadline_job.json，
    # 农场端的 run_asb_deadline_job 读这个文件完成单个子资产的发布。
    #
    # 依赖 create_sub_asset_and_record 回写的 id / model_task_id，
    # 并把 deadline_job_file 路径回写进 gen_asset_data 供 submit_asb_deadline_task 使用。
    try:
        tc = TaskContext(process_data['task_id']) or TaskContext.from_env()
        version_dir = process_data["version_dir"]
        gen_asset_data = process_data["gen_asset_data"]
        root = process_data["root"]
        user = process_data["user"]

        deadline_job_dir = os.path.join(version_dir, 'deadline_job')
        if not os.path.exists(deadline_job_dir):
            os.makedirs(deadline_job_dir)

        # ENV 占位按它挂在哪个层级下归类。读节点 notes 要走主线程
        env_placeholders = utils.executeInMainThreadWithResult(
            lambda: get_asb_nodes.get_env_placeholders(
                root_longname=root.longName(),
                project_name=tc.project_name))
        if env_placeholders:
            logger.info(u"ENV 占位: {0}".format(env_placeholders))

        for sub_asset_name, asset_info in gen_asset_data.items():
            sub_assets_data = [
                {'longname': s_asset_name,
                 'model_task_id': gen_asset_data[s_asset_name.split('|')[-1]]['model_task_id']}
                for s_asset_name in asset_info['sub_assets']
            ]

            # 只有 ASB 才做 USD 组装，PROP 不需要 ENV 数据
            env_assets_data = []
            if asset_info['asset_type'] == 'ASB':
                env_assets_data = env_placeholders.get(asset_info['longname'], [])

            json_file = os.path.join(
                deadline_job_dir,
                '{0}.{1}.deadline_job.json'.format(asset_info['asset_type'], sub_asset_name))
            gen_asset_data[sub_asset_name]['deadline_job_file'] = json_file

            json_data = {
                'source_file': os.path.join(version_dir, 'source.ma'),
                'thumb_file': os.path.join(version_dir, 'snapshot',
                                           '{0}.png'.format(sub_asset_name)),
                'longname': asset_info['longname'],
                'asset_id': asset_info['id'],
                'asset_name': sub_asset_name,
                'asset_type': asset_info['asset_type'],
                'sub_assets_data': sub_assets_data,
                'env_assets_data': env_assets_data,
                'model_task_id': asset_info['model_task_id'],
                'user': user,
            }

            with open(json_file, 'w') as f:
                json.dump(json_data, f, indent=4)

        logger.info(u"已生成 {0} 个 Deadline 任务描述文件，目录: {1}".format(
            len(gen_asset_data), deadline_job_dir))

    except:
        return traceback.format_exc()
