# -*- coding: utf-8 -*-
import os
import traceback

import maya.cmds as cmds
import maya.utils as utils
from qtpy import QtCore, QtWidgets

from oct_maya.utils.maya_utils import gen


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查文件内引用的资源路径（贴图 / 声音）是否丢失或指向本地
    """
    # 资源路径指向本地盘或文件不存在都会报错，不允许跳过。
    # Fix：本地资源拷到工作目录 sourceimages 下并改路径；丢失的资源询问后删除节点。
    try:
        def check():
            all_resources = gen.get_all_resoucre_paths()
            missing_dict, missing_resources = gen.list_missing_resources(all_resources)
            local_dict, local_resources = gen.list_local_resources(all_resources)

            detail_msg = ''
            if missing_resources:
                detail_msg += u'文件内存在 {0} 个路径丢失的节点: \n'.format(len(missing_resources))
                for node_attr, file_path in missing_resources:
                    detail_msg += node_attr + ': ' + file_path + '\n'
                cmds.select([node_attr.split('.')[0] for node_attr, _ in missing_resources])

            if local_resources:
                detail_msg += u'文件内存在 {0} 个路径指向本地的节点: \n'.format(len(local_resources))
                for node_attr, file_path in local_resources:
                    detail_msg += node_attr + ': ' + file_path + '\n'
            return detail_msg

        detail_msg = utils.executeInMainThreadWithResult(check)
        if detail_msg:
            return detail_msg + u"\n请点击 Fix：本地资源会拷贝到工作目录，丢失的资源会询问是否删除节点"
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """本地资源拷贝到工作目录 sourceimages 下；丢失的资源询问后删除节点"""
    try:
        work_file = (submit_data.get('ma_file') or '').replace('\\', '/')
        dest_dir = os.path.join(os.path.dirname(work_file), 'sourceimages').replace('\\', '/')

        def repair():
            all_resources = gen.get_all_resoucre_paths()
            missing_dict, missing_resources = gen.list_missing_resources(all_resources)
            local_dict, local_resources = gen.list_local_resources(all_resources)

            if local_resources:
                progress = QtWidgets.QProgressDialog(u"正在拷贝本地资源...", u"取消", 0,
                                                     len(local_resources), parent_widget)
                progress.setWindowModality(QtCore.Qt.WindowModal)
                progress.setValue(0)
                progress.show()
                try:
                    path_info = gen.copy_local_resources(local_dict, dest_dir, progress)
                finally:
                    progress.setValue(len(local_resources))
                    progress.deleteLater()
                for node_attr, (old_path, new_path) in path_info.items():
                    logger.info(u"AUTO FIX: {0}: {1} -> {2}".format(node_attr, old_path, new_path))

            if missing_resources:
                missing_nodes = [node_attr.split('.')[0] for node_attr, _ in missing_resources]
                msg = u'文件内存在 {0} 个路径丢失的节点，是否要删除这些节点？\n{1}'.format(
                    len(missing_nodes), '\n'.join(missing_nodes))
                result = cmds.confirmDialog(title='Warning', message=msg, button=[u'是', u'否'],
                                            defaultButton=u'否', cancelButton=u'否', dismissString=u'否')
                if result == u'是':
                    cmds.delete(missing_nodes)
                    logger.info(u"AUTO FIX: 删除路径丢失的节点 {0}".format(' '.join(missing_nodes)))
                else:
                    return u"路径丢失的节点未处理，请手动修正路径或删除节点"
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
