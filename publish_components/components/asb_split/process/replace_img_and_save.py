# -*- coding: utf-8 -*-
import os
import traceback

import pymel.core as pm

from publish_components.utils.texture_files import TEXTURE_NODE_ATTRS, set_texture_path


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    替换贴图路径到I:盘工程目录下的sourceimage，然后保存
    """
    # 贴图已由 copy_asb_asset_images 拷进版本目录的 sourceimages，
    # 这里把节点上的绝对路径改成相对路径再存盘。仅农场端使用。
    try:
        if not pm.pluginInfo('mtoa', q=True, loaded=True):
            pm.loadPlugin('mtoa', quiet=True)

        # copy_asb_asset_images 里同名贴图按哈希改过名的节点: {节点.属性: 新文件名}
        rename_map = process_data.get('tex_rename') or {}

        replaced = 0
        for node in pm.ls(type=['file', 'aiImage']):
            attr_name = TEXTURE_NODE_ATTRS.get(node.type())
            file_path = node.attr(attr_name).get()

            # 已经在 I 盘或已是相对路径的跳过
            if (file_path.startswith('I:') or file_path.startswith('i:')
                    or file_path.startswith('sourceimages')):
                continue

            node_attr = node.name() + '.' + attr_name
            new_name = rename_map.get(node_attr, os.path.basename(file_path.replace('\\', '/')))
            new_file_path = 'sourceimages/{0}'.format(new_name)
            logger.info(u"替换贴图路径: {0} -> {1}".format(file_path, new_file_path))
            # 改路径会让 Maya 按文件名重新推断 colorSpace，set_texture_path 会把原值设回去
            set_texture_path(node_attr, new_file_path)
            replaced += 1

        pm.saveFile(force=True)
        logger.info(u"已替换 {0} 个贴图路径并保存".format(replaced))

    except:
        return traceback.format_exc()
