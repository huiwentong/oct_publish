# -*- coding: utf-8 -*-
import os
import shutil
import traceback

import maya.utils as utils

from oct_maya.tools.lay.usd_lay_manager_new.core import is_old_asb_architecture
from publish_components.utils.maya_utils import shot_usd


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    把 Stage 引用的 maya_usd 目录下的 usda 拷贝到版本目录
    """
    # 老 lay/copy_usd_file_to_v_dir：W 盘工作目录 maya_usd/xxx.usda -> I 盘版本目录 maya_usd/xxx.usda。
    # 旧架构 Stage 不拷。
    try:
        source_file = (submit_data.get('ma_file') or '').replace('\\', '/')
        if not source_file or not os.path.isfile(source_file):
            return u"工作文件不存在: {0}".format(source_file)
        work_dir = os.path.dirname(source_file)
        publish_dir = process_data['version_dir'].replace('\\', '/')

        def read_proxies():
            if is_old_asb_architecture():
                return None
            return shot_usd.list_proxy_usd_paths()

        proxies = utils.executeInMainThreadWithResult(read_proxies)
        copied = set()
        for proxy_shape, usd_path in proxies or []:
            usd_path = shot_usd.normalize_usd_path(usd_path)
            if not usd_path:
                continue
            # filePath 可能是绝对路径也可能是相对路径，统一用文件名拼出版本目录下的相对位置
            rel_path = 'maya_usd/{0}'.format(os.path.basename(usd_path))
            if rel_path in copied:
                continue
            copied.add(rel_path)

            src_usda = shot_usd.resolve_usd_abs_path(usd_path, work_dir)
            dst_usda = '{0}/{1}'.format(publish_dir.rstrip('/'), rel_path)
            if not os.path.isfile(src_usda):
                return u"USD 源文件不存在: {0} (节点: {1})".format(src_usda, proxy_shape)

            os.makedirs(os.path.dirname(dst_usda), exist_ok=True)
            shutil.copyfile(src_usda, dst_usda)
            logger.info(u"拷贝 USD 文件: {0} -> {1}".format(src_usda, dst_usda))
    except:
        return traceback.format_exc()
