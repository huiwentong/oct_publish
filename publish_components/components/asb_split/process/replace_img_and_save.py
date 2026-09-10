# -*- coding: utf-8 -*-
import os
import traceback

import pymel.core as pm


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    替换贴图路径到I:盘工程目录下的sourceimage，然后保存
    """
    # 贴图已由 copy_asset_images 拷进版本目录的 sourceimages，
    # 这里把节点上的绝对路径改成相对路径再存盘。仅农场端使用。
    try:
        if not pm.pluginInfo('mtoa', q=True, loaded=True):
            pm.loadPlugin('mtoa', quiet=True)

        attr_map = {'file': 'fileTextureName', 'aiImage': 'filename'}
        replaced = 0
        for node in pm.ls(type=['file', 'aiImage']):
            attr_name = attr_map.get(node.type())
            file_path = node.attr(attr_name).get()

            # 已经在 I 盘或已是相对路径的跳过
            if (file_path.startswith('I:') or file_path.startswith('i:')
                    or file_path.startswith('sourceimages')):
                continue

            new_file_path = 'sourceimages/{0}'.format(os.path.basename(file_path))
            logger.info(u"替换贴图路径: {0} -> {1}".format(file_path, new_file_path))
            node.setAttr(attr_name, new_file_path, type='string')
            replaced += 1

        pm.saveFile(force=True)
        logger.info(u"已替换 {0} 个贴图路径并保存".format(replaced))

    except:
        return traceback.format_exc()
