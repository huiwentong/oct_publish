# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    把文件内被 copy_resources_to_v_dir 改过的资源路径重新指回工作目录
    """

    try:
        modified = process_data.get('modified_resources_info') or {}

        def restore():
            for node_attr, path_list in modified.items():
                cmds.setAttr(node_attr, path_list[0], type='string')
                logger.info(u"{0} -> {1}".format(node_attr, path_list[0]))

        utils.executeInMainThreadWithResult(restore)
    except:
        return traceback.format_exc()
