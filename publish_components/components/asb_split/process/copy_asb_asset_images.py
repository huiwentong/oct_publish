# -*- coding: utf-8 -*-
import os
import shutil
import traceback

import maya.utils as utils
import pymel.core as pm

from publish_components.utils.texture_files import (TextureFileResolver, add_suffix, assign_suffixes,
                                                    get_asset_texture_nodes, group_textures)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    拷贝资产的贴图到 I: 版本文件夹，同名贴图按哈希改名
    """
    # 与通用的 maya_gen/copy_asset_images 的区别：贴图统一扁平拷进 sourceimages 时，不同目录下的
    # 同名贴图会互相覆盖。这里按文件名分组，同名但内容不同的贴图按文件 md5 加后缀区分
    # （a.jpg -> a_1f3c9e2b.jpg），同名同内容的只拷一份、保持原名。
    # 处理结果记录到 process_data['tex_rename'] = {节点.属性: 目标文件名}（没改名的记原名），
    # 由下游写回节点：主 ASB 阶段是 export_asb_source_scene，农场端是 replace_img_and_save。
    try:
        v_dir_imgs = process_data['v_dir_imgs'].replace('\\', '/')
        if not os.path.isdir(v_dir_imgs):
            os.makedirs(v_dir_imgs)

        def collect():
            """节点遍历和路径解析都走 Maya API，必须回主线程。

            GUI 模式下组件跑在 ComponentWorker 的 QThread 里，直接调 Maya 会随机闪退；
            农场端是 mayapy 单线程才没暴露这个问题。resolver 的目录扫描也一起留在这里，
            和 check_textures_in_work_dir 的划分保持一致。
            """
            resolver = TextureFileResolver()
            texture_nodes = get_asset_texture_nodes(pm.PyNode(process_data['root']))
            return group_textures(texture_nodes, resolver, logger)

        groups = utils.executeInMainThreadWithResult(collect)

        # 往下只剩 md5 计算和文件拷贝，纯 IO，留在后台线程跑，不占着主线程卡 UI
        tex_rename = {}
        for info in groups.values():
            info['dest_dir'] = v_dir_imgs
        assign_suffixes(groups, logger)

        copied = set()
        for info in groups.values():
            suffix = info['suffix']

            # 同一套贴图（内容相同）已经拷过就不再拷
            for src_file in info['files']:
                src_name = os.path.basename(src_file)
                dst_name = add_suffix(src_name, suffix) if suffix else src_name
                dst_file = v_dir_imgs + '/' + dst_name
                if dst_file.lower() in copied:
                    continue
                copied.add(dst_file.lower())
                shutil.copyfile(src_file, dst_file)

            # 记录每个节点最终要指向的文件名，保持原属性值的写法（具体某一块 UDIM 或占位符）。
            # 没改名的也记，这样下游不用自己判断该用新名还是 basename
            for node_attr, raw_path in info['nodes']:
                raw_name = os.path.basename(raw_path.replace('\\', '/'))
                tex_rename[node_attr] = add_suffix(raw_name, suffix) if suffix else raw_name

        process_data['tex_rename'] = tex_rename
        logger.info(u'资产 {0} 共拷贝 {1} 个贴图文件，记录 {2} 个贴图节点'.format(
            process_data.get('entity_name', ''), len(copied), len(tex_rename)))

    except Exception:
        return traceback.format_exc()
