# -*- coding: utf-8 -*-
import os
import shutil
import traceback
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """拷贝 ASB 工程文件及新版 Stage 的相对 USD 文件"""
    try:
        source = submit_data['ma_file']
        target = process_data['v_dir_ma_file']
        tc = TaskContext(process_data['task_id'])
        def collect_paths():
            root, legacy, proxies = asb_build.scene_info(tc.entity_name)
            if legacy:
                return []
            if asb_build.dirty_proxies(proxies):
                raise RuntimeError('发布前 USD 又有未保存修改，请重新检查')
            return asb_build.proxy_paths(proxies, source)
        relative_paths = utils.executeInMainThreadWithResult(collect_paths)
        copies = [(source, target)]
        for relative in relative_paths:
            copies.append((os.path.join(os.path.dirname(source), relative),
                           os.path.join(os.path.dirname(target), relative)))
        # 先验证所有源文件，避免复制一半才发现缺少 Stage 文件。
        for src, dst in copies:
            if not os.path.isfile(src):
                raise RuntimeError('发布源文件不存在: ' + src)
            if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst)):
                raise RuntimeError('发布目标不能覆盖工作文件: ' + src)
        for src, dst in copies:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            logger.info('拷贝文件: {0} -> {1}'.format(src, dst))
        process_data['asb_exported_files'] = [dst for src, dst in copies]
    except Exception:
        return traceback.format_exc()
