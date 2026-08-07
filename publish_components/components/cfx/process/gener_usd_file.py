# -*- coding:utf-8 -*-
"""
===========================================
项目名称: int
文件: copy_rig_file
作者: huiwentong
创建时间: 2025/10/10
版本: 1.0.0
联系方式: 1120267329@qq.com
描述:
    ******
===========================================
"""

# -*- coding: utf-8 -*-

import os
import traceback
from oct.data.usd import step_pub_usds


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
生成 USD文件
    """
    try:
        import hou
        rig_file = process_data['version_dir'] + '/' + os.path.basename(hou.hipFile.path())
        step_pub_usds.CfxStepUsd(process_data['version_dir'], process_data['task_id'], rig_file)
    except:
        return traceback.format_exc()


