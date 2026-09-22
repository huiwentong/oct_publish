# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils

from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import asb_build


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 ASB 是否为新架构（|资产名 下只挂一个 USD Stage），旧版多 Stage 架构不允许发布"""
    # 判定规则与 super_usd_assembly_new.core.is_old_architecture 相同：根组下有非 proxyShape 的子节点即旧架构。
    # 后面的 check_usd_relative_path / copy_usd_file_to_v_dir / edit_ma_file 都只按单 Stage 的 sidecar 处理，
    # 旧架构走到那里会把发布目录里的壳 usda 当 sidecar 拷走，所以在这里拦住。
    #
    # 不提供 Fix：ASB 组装工具的 convert_old_to_new_arch 会删掉旧顶层组并把 Maya / USD 另存为下一个版本号，
    # 是带确认框的一次性操作，不该在检查阶段悄悄发生；转换后也必须用新版本文件重新走发布。
    try:
        tc = TaskContext(process_data['task_id'])
        legacy = utils.executeInMainThreadWithResult(
            lambda: asb_build.scene_info(tc.entity_name)[1])
        if legacy:
            return (u"当前 ASB 为旧架构（多个 Stage 分别挂在子组下），不允许发布。\n"
                    u"请在 ASB 组装工具中点击“转换旧架构”，转换会把 Maya 和 USD 另存为下一个版本，"
                    u"之后请重新打开发布工具")
    except Exception:
        return traceback.format_exc()
