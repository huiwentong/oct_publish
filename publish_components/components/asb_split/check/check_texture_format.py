# -*- coding: utf-8 -*-
import os
import traceback

import maya.cmds as cmds
import maya.utils as utils

from publish_components.utils.texture_files import (ALLOWED_FORMATS, EXPECTED_CONTENT_FORMATS, TEXTURE_NODE_ATTRS,
                                                    TextureFileResolver, detect_texture_format,
                                                    resolve_texture_pattern)


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查贴图格式
    """
    # 场景里所有 file / aiImage 节点引用的贴图，只允许常规扩展名（见 ALLOWED_FORMATS），
    # 并且文件扩展名必须与实际内容一致（按文件头识别）。
    # dds、webp、psd 等格式以及 .jfif 扩展名不符合发布规范，需转成 png / jpg / tif / exr。
    # 报错时把有问题的贴图节点选中，方便在大纲 / Hypershade 里定位。
    try:
        def check():
            errors = []
            bad_nodes = []
            resolver = TextureFileResolver()
            detected_format_cache = {}

            for node_type, attr_name in TEXTURE_NODE_ATTRS.items():
                try:
                    nodes = cmds.ls(type=node_type) or []
                except RuntimeError:
                    # 对应插件（如 mtoa）没加载时节点类型不存在
                    nodes = []

                for node in nodes:
                    tex_path, resolved_pattern = resolve_texture_pattern(node, attr_name)
                    if not tex_path.strip():
                        continue

                    ext = os.path.splitext(os.path.basename(tex_path.replace('\\', '/')))[-1].lstrip('.').lower()
                    # 贴图节点下游连到的材质球，报错时一起列出来
                    downstream = cmds.listHistory(node, future=True) or []
                    shading_groups = cmds.ls(downstream, type='shadingEngine') or []
                    used_by = u"、".join(shading_groups) if shading_groups else u"未连接到材质"

                    if ext not in ALLOWED_FORMATS:
                        bad_nodes.append(node)
                        errors.append(u"贴图节点 {0}（材质: {1}）\n    格式: {2}    路径: {3}".format(
                            node, used_by, ext or u"无扩展名", tex_path))
                        continue

                    mismatches = []
                    for file_path in resolver.find_files(resolved_pattern):
                        cache_key = os.path.normcase(os.path.normpath(file_path))
                        if cache_key not in detected_format_cache:
                            detected_format_cache[cache_key] = detect_texture_format(file_path)
                        actual_format = detected_format_cache[cache_key]

                        # 无法可靠识别时跳过，避免旧版 TGA 等格式被误报
                        if actual_format and actual_format not in EXPECTED_CONTENT_FORMATS[ext]:
                            mismatches.append(u"    扩展名: {0}    实际格式: {1}    文件: {2}".format(
                                ext, actual_format, file_path))

                    if mismatches:
                        bad_nodes.append(node)
                        errors.append(u"贴图节点 {0}（材质: {1}）扩展名与文件内容不一致:\n{2}".format(
                            node, used_by, u"\n".join(mismatches)))

            if errors:
                # 选中有问题的贴图节点，用户在大纲 / Hypershade 里可以直接看到
                cmds.select(list(dict.fromkeys(bad_nodes)), replace=True)

            return errors, len(set(bad_nodes))

        errors, bad_count = utils.executeInMainThreadWithResult(check)
        if errors:
            return u"以下 {0} 个贴图节点的格式有问题。已在场景中选中这些节点:\n{1}".format(
                bad_count, u"\n".join(errors))

    except Exception:
        return traceback.format_exc()
