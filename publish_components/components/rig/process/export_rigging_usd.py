#!/usr/bin/env python  
# -*- coding:utf-8 -*-
import os
import json
import traceback
import maya.utils as utils
from oct.data.usd.step_pub_usds import RigStepUsd


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
导出绑定环节usd文件
    """
    try:
        def process():
            version_dir = process_data.get('version_dir', '')
            task_id = process_data.get('task_id', '')
            v_dir_ma_file = process_data.get('v_dir_ma_file', '')

            RigStepUsd(
                version_folder=version_dir,
                task_id=task_id,
                rig_file=v_dir_ma_file,
            )

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
