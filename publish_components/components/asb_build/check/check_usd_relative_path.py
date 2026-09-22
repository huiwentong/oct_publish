# -*- coding: utf-8 -*-
import os
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build, shot_usd


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 ASB Stage 引用的 usda 路径：必须是工作目录 maya_usd 下与 Maya 文件同名的 usda，且文件存在"""
    try:
        maya_file = (submit_data.get('ma_file') or '').replace('\\', '/')
        if not maya_file:
            return u"无法获取当前 Maya 工程文件名"
        work_dir = os.path.dirname(maya_file)
        tc = TaskContext(process_data['task_id'])

        def check():
            root, legacy, proxies = asb_build.scene_info(tc.entity_name)
            errors = []
            for proxy_shape in proxies:
                usd_path = cmds.getAttr(proxy_shape + '.filePath') or ''
                err = shot_usd.validate_usd_path(usd_path, maya_file)
                if err:
                    errors.append(u"{0}:\n  {1}".format(proxy_shape, err))
                    continue
                abs_usd_path = shot_usd.resolve_usd_abs_path(usd_path, work_dir)
                if not os.path.isfile(abs_usd_path):
                    errors.append(u"{0}:\n  USD 文件不存在: {1}".format(proxy_shape, abs_usd_path))
            if errors:
                return u"USD 引用路径检查未通过，请点击 Fix 修复:\n{0}".format('\n'.join(errors))
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """把 Stage 的 filePath 改为 maya_usd/<工作文件名>.usda，缺文件时从当前 layer 拷一份"""
    try:
        tc = TaskContext(process_data['task_id'])

        def repair():
            root, legacy, proxies = asb_build.scene_info(tc.entity_name)
            repairs, paths = asb_build.repair_proxy_paths(proxies, submit_data['ma_file'])
            return repairs

        for proxy, old_path, new_path in utils.executeInMainThreadWithResult(repair):
            logger.info(u'AUTO FIX: {0}: {1} -> {2}'.format(proxy, old_path, new_path))
    except Exception:
        return traceback.format_exc()
