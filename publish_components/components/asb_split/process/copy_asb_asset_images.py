# -*- coding: utf-8 -*-
import os
import shutil
import traceback

import pymel.core as pm

from publish_components.utils.maya_utils import get_upstream_nodes
from publish_components.utils.texture_files import (TEXTURE_NODE_ATTRS, TextureFileResolver, add_suffix,
                                                    assign_collision_suffixes, resolve_texture_pattern)

# 文件名后缀取 md5 的前几位，足够区分又不会让文件名太长
HASH_LENGTH = 8


def get_asset_texture_nodes(n_root):
    """
    找出资产层级下用到的贴图节点，按 shadingEngine 的上游节点判断，与 maya_gen/copy_asset_images 一致。

    Args:
        n_root: PyNode, 资产根层级

    Returns:
        list, [(节点名, 属性名), ...]，去重
    """
    root_path = n_root.fullPath() + '|'
    texture_nodes = []
    seen = set()
    for se in pm.ls(type='shadingEngine'):
        upstream = get_upstream_nodes.get_nodes(se)
        if not any(node_path.startswith(root_path) for node_path in upstream):
            continue
        for node_path in upstream:
            node = pm.PyNode(node_path)
            attr_name = TEXTURE_NODE_ATTRS.get(node.nodeType())
            if attr_name and node.name() not in seen:
                seen.add(node.name())
                texture_nodes.append((node.name(), attr_name))

    return texture_nodes


def group_textures(texture_nodes, resolver, logger):
    """
    按解析后的路径模式归并贴图节点，同一套贴图被多个节点引用时只处理一次。

    Returns:
        dict, {pattern小写: {'pattern', 'files', 'nodes': [(node_attr, raw_path), ...]}}
    """
    groups = {}
    for node, attr_name in texture_nodes:
        raw_path, pattern = resolve_texture_pattern(node, attr_name)
        if not pattern:
            continue

        key = pattern.lower()
        if key not in groups:
            files = resolver.find_files(pattern)
            if not files:
                logger.warning(u'贴图不存在，跳过: {0}.{1} = {2}'.format(node, attr_name, raw_path))
                groups[key] = None
            else:
                groups[key] = {'pattern': pattern, 'files': files, 'nodes': []}

        if groups[key]:
            groups[key]['nodes'].append((node + '.' + attr_name, raw_path))

    return {key: info for key, info in groups.items() if info}


def assign_suffixes(groups, logger):
    """
    找出文件名相同的贴图组，同名同内容的合并，同名不同内容的给每组分配哈希后缀。

    Args:
        groups: dict, group_textures 的结果，会就地给每组加上 'suffix' 键（没冲突为空字符串）
    """
    conflict_count = assign_collision_suffixes(groups.values(), hash_length=HASH_LENGTH)
    if not conflict_count:
        return

    logger.info(u'检测到实际输出文件名冲突，{0} 组贴图按哈希改名:'.format(conflict_count))
    for info in groups.values():
        if info['suffix']:
            logger.info(u'   {0} -> {1}'.format(
                info['pattern'], add_suffix(os.path.basename(info['pattern']), info['suffix'])))


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    拷贝资产的贴图到 I: 版本文件夹，同名贴图按哈希改名
    """
    # 与通用的 maya_gen/copy_asset_images 的区别：贴图统一扁平拷进 sourceimages 时，不同目录下的
    # 同名贴图会互相覆盖。这里按文件名分组，同名但内容不同的贴图按文件 md5 加后缀区分
    # （a.jpg -> a_1f3c9e2b.jpg），同名同内容的只拷一份、保持原名。
    # 改名结果记录到 process_data['tex_rename'] = {节点.属性: 新文件名}，由 replace_img_and_save 写回节点。
    #
    # 通用的 copy_asset_images 被 mod / rig 等多个环节共用，它们后面按文件名改路径，
    # 所以不能直接在那边改名，单独做一份 asb 专用的。仅农场端使用。
    try:
        v_dir_imgs = process_data['v_dir_imgs'].replace('\\', '/')
        if not os.path.isdir(v_dir_imgs):
            os.makedirs(v_dir_imgs)

        resolver = TextureFileResolver()
        tex_rename = {}

        texture_nodes = get_asset_texture_nodes(pm.PyNode(process_data['root']))
        groups = group_textures(texture_nodes, resolver, logger)
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

            # 记录节点要写回的文件名，保持原属性值的写法（具体某一块 UDIM 或占位符）
            if suffix:
                for node_attr, raw_path in info['nodes']:
                    raw_name = os.path.basename(raw_path.replace('\\', '/'))
                    tex_rename[node_attr] = add_suffix(raw_name, suffix)

        process_data['tex_rename'] = tex_rename
        logger.info(u'资产 {0} 共拷贝 {1} 个贴图文件，{2} 个节点改名'.format(
            process_data.get('entity_name', ''), len(copied), len(tex_rename)))

    except Exception:
        return traceback.format_exc()
