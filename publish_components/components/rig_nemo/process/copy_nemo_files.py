#!/usr/bin/env python  
# -*- coding:utf-8 -*-
import traceback
import os
import shutil
import maya.utils as utils
import maya.cmds as mc


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
拷贝NemoRig数据文件到版本文件夹
    """
    try:
        def process():
            target_dir = os.path.join(process_data.get('version_dir'), 'data').replace('\\', '/')
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)

            shutil.copy2(process_data['nemo_json'], target_dir)
            shutil.copy2(process_data['mat_json'], target_dir)
            shutil.copy2(process_data['dll'], target_dir)
            shutil.copy2(process_data['resource'], target_dir)
            if process_data.get('export'):  # ***_EXPORT.zip
                shutil.copy2(process_data['export'], target_dir)

            mc.setAttr(process_data['nemo_node'] + '.nemo',
                       os.path.join(target_dir, os.path.basename(process_data['nemo_json'])).replace('\\', '/'),
                       type='string')
            mc.setAttr(process_data['nemo_node'] + '.shading',
                       os.path.join(target_dir, os.path.basename(process_data['mat_json'])).replace('\\', '/'),
                       type='string')

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
