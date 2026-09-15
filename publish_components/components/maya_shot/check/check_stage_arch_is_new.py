# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct.pipeline.task_context import TaskContext
from oct_maya.tools.lay.usd_lay_manager_new.core import (
    convert_asb_old_to_new_arch,
    convert_asb_old_to_new_arch_for_layout,
    is_old_asb_architecture,
)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 USD Stage 是否为新架构（单一 Stage，用 usd reference 引用多个资产）
    """
    # 新架构是一个 Stage 通过 usd reference 引用多个资产；每个资产各挂一个 Stage 的旧架构不再支持。
    try:
        if utils.executeInMainThreadWithResult(is_old_asb_architecture):
            return u"当前 Stage 为旧架构，请点击 Fix 转换为新架构"
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """把旧架构 ASB Stage 转换为新架构"""
    try:
        tc = TaskContext(process_data['task_id'])
        # Step.code：lay 环节是 'ly'，Bk / An 走 layout 版本的转换
        step_code = tc.step_name

        def repair():
            if not cmds.file(q=True, sn=True):
                return u"请先保存 Maya 文件后再执行转换"
            if not is_old_asb_architecture():
                logger.info(u"当前 ASB 已是新架构，无需转换")
                return ""
            try:
                if step_code in ['ly']:
                    convert_asb_old_to_new_arch()
                else:
                    convert_asb_old_to_new_arch_for_layout()
            except RuntimeError as e:
                return str(e)
            logger.info(u"AUTO FIX: ASB Stage 已转换为新架构")
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
