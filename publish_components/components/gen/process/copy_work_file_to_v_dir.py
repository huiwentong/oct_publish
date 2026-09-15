# -*- coding: utf-8 -*-
import os
import shutil
import traceback

from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    向版本文件夹拷贝工程文件
    """
    # 老 gen/copy_work_file_to_v_dir：资产按 <资产名>.<ext>，镜头按 <版本名>.<ext> 命名。
    # 工程文件优先取表单里的 ma_file（Maya 环节），没有则取 CLI 传入的 dcc_file。
    try:
        source_file = (submit_data.get('ma_file') or process_data.get('dcc_file') or '').replace('\\', '/')
        if not source_file or not os.path.isfile(source_file):
            return u"工作文件不存在: {0}".format(source_file)

        tc = TaskContext(process_data['task_id'])
        version_dir = process_data['version_dir']
        ext = source_file.rsplit('.', 1)[-1]
        if tc.entity_type == 'Asset':
            target_file = '{0}/{1}.{2}'.format(version_dir, tc.entity_name, ext)
        else:
            target_file = '{0}/{1}.{2}'.format(version_dir, process_data['version_name'], ext)

        shutil.copyfile(source_file, target_file)
        logger.info(u"拷贝工程文件: {0} -> {1}".format(source_file, target_file))
    except:
        return traceback.format_exc()
