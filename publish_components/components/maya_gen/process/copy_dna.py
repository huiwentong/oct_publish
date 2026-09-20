# -*- coding:utf-8 -*-

import traceback
import os, shutil
import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
文件中如果调用dna文件，拷贝dna到publish目录下
    """
    try:
        def process():
            if cmds.ls(type='embeddedNodeRL4'):
                version_dir = process_data.get('version_dir', '')
                node = cmds.ls(type='embeddedNodeRL4')[0]
                local_dna = cmds.getAttr(node + '.dnaFilePath')
                if os.path.isfile(local_dna):
                    dest_dna = os.path.join(version_dir, os.path.basename(local_dna)).replace('\\', '/')
                    shutil.copy2(local_dna, dest_dna)

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result
    except:
        return traceback.format_exc()
