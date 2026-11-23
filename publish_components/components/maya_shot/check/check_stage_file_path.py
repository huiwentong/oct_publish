# -*- coding: utf-8 -*-
import os
import traceback

import maya.utils as utils

from oct_maya.tools.lay.usd_lay_manager_new.core import bump_asb_usd_to_maya_version, is_old_asb_architecture
from publish_components.utils.maya_utils import shot_usd

WORLD_ROOT = '|World|'


def list_world_proxy_usd_paths():
    """只取 |World 下的 Stage，World 外的临时/参考 Stage 不参与检查"""
    return [(shape, path) for shape, path in shot_usd.list_proxy_usd_paths() if shape.startswith(WORLD_ROOT)]


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 Stage 引用的 usda 路径：必须在工作文件同目录 maya_usd 下、与 Maya 文件同名，且文件存在
    """
    # Stage 的 filePath 可能是相对路径也可能是绝对路径，统一解析后和工作文件同名的 usda 比较。
    try:
        maya_file = (submit_data.get('ma_file') or '').replace('\\', '/')
        if not maya_file:
            return u"无法获取当前 Maya 工程文件名"
        work_dir = os.path.dirname(maya_file)

        def check():
            proxies = list_world_proxy_usd_paths()
            if not proxies:
                # |World 下没有 mayaUsdProxyShape 节点
                return ""
            if is_old_asb_architecture():
                return u"请先将 USD Stage 转换为新架构"

            errors = []
            for proxy_shape, usd_path in proxies:
                err = shot_usd.validate_usd_path(usd_path, maya_file)
                if err:
                    errors.append(u"{0}:\n  {1}".format(proxy_shape, err))
                    continue
                abs_usd_path = shot_usd.resolve_usd_abs_path(usd_path, work_dir)
                if not os.path.isfile(abs_usd_path):
                    errors.append(u"{0}:\n  USD 文件不存在: {1}".format(proxy_shape, abs_usd_path))

            if errors:
                return u"USD 引用路径检查未通过，请点击 Fix 或用 Layout USD 管理器修正:\n{0}".format('\n'.join(errors))
            return ""

        result = utils.executeInMainThreadWithResult(check)
        if result:
            return result
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """把 Stage 引用的 usda 提升到与当前 Maya 文件一致的版本"""
    try:
        maya_file = (submit_data.get('ma_file') or '').replace('\\', '/')
        work_dir = os.path.dirname(maya_file)

        def repair():
            if is_old_asb_architecture():
                return u"请先将 USD Stage 转换为新架构"
            for proxy_shape, usd_path in list_world_proxy_usd_paths():
                abs_usd_path = shot_usd.resolve_usd_abs_path(usd_path, work_dir)
                if not os.path.isfile(abs_usd_path):
                    return u"USD 文件不存在，无法自动修复: {0}".format(abs_usd_path)
            bump_asb_usd_to_maya_version()
            logger.info(u"AUTO FIX: Stage 引用的 usda 已同步到当前 Maya 文件版本")
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
