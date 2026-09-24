# -*- coding: utf-8 -*-
import os
import traceback

import maya.utils as utils
import pymel.core as pm

from publish_components.utils.texture_files import TEXTURE_NODE_ATTRS, set_texture_path


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    导出原始的asb总文件
    """
    # 把 ASB 根层级整体导出成 source.ma，农场端的每个子资产任务都从这个文件出发。
    # 导出前把贴图路径临时指向版本目录里 copy_asb_asset_images 拷好的那份，导出完立刻改回。
    try:
        version_dir = process_data["version_dir"]
        root = process_data["root"]
        v_dir_imgs = process_data["v_dir_imgs"].replace(os.sep, '/')
        # {节点.属性: 目标文件名}，由 copy_asb_asset_images 写入
        tex_rename = process_data.get('tex_rename') or {}

        def export():
            target_file = os.path.join(version_dir, 'source.ma')
            # 替换和导出必须共用一个 try：替换到一半失败时，已经改掉的节点也要还原，
            # 否则美术的场景就停在部分指向版本目录的状态
            old_paths = {}
            try:
                # 只动 copy_asb_asset_images 处理过的节点 —— 没拷过去的贴图指过去就是死链。
                # 必须写绝对路径：农场端打开 source.ma 时不设 Maya 工程，相对路径解析不到
                for node in pm.ls(type=['file', 'aiImage']):
                    attr_name = TEXTURE_NODE_ATTRS.get(node.type())
                    if not attr_name:
                        continue
                    node_attr = node.name() + '.' + attr_name
                    if node_attr not in tex_rename:
                        continue
                    # 先把原值记进 old_paths 再改，这一步的顺序决定了中途失败能不能还原
                    old_paths[node_attr] = node.attr(attr_name).get()
                    # set_texture_path 会把 colorSpace 设回去：改路径会让 Maya 重新推断它
                    set_texture_path(node_attr, v_dir_imgs + '/' + tex_rename[node_attr])

                pm.select(root, r=True)
                pm.exportSelected(target_file,
                                  force=True,
                                  options="v=0;",
                                  type="mayaAscii",
                                  pr=True,
                                  es=True)
                pm.select(cl=True)
                logger.info(u"source.ma 的 {0} 个贴图节点已指向版本目录".format(len(old_paths)))
            finally:
                # 单个节点还原失败不能连累其它节点，逐个兜住并记日志
                for node_attr, old_path in old_paths.items():
                    try:
                        set_texture_path(node_attr, old_path)
                    except Exception:
                        logger.error(u"贴图路径还原失败，请手动检查: {0} -> {1}".format(
                            node_attr, old_path))
            return target_file

        target_file = utils.executeInMainThreadWithResult(export)
        logger.info(u"已导出 ASB 总文件: {0}".format(target_file))

    except:
        return traceback.format_exc()
