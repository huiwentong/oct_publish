# -*- coding: utf-8 -*-
import traceback

import maya.utils as utils

from oct_maya.utils.maya_utils.gen import copy_local_resources, get_all_resoucre_paths


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    拷贝文件内的示意贴图、声音到版本文件夹，并把场景里的路径指向版本目录
    """
    # 老 maya/copy_resources_to_v_dir。改过的路径记录在 process_data['modified_resources_info']，
    # 工作文件拷进版本目录后由 restore_resource_path 改回工作目录的路径。
    try:
        version_dir = process_data['version_dir']

        def process():
            all_resources = get_all_resoucre_paths()
            return copy_local_resources(all_resources, version_dir)

        modified = utils.executeInMainThreadWithResult(process)
        process_data['modified_resources_info'] = modified
        for node_attr, (old_path, new_path) in modified.items():
            logger.info(u"{0}: {1} -> {2}".format(node_attr, old_path, new_path))
    except:
        return traceback.format_exc()
