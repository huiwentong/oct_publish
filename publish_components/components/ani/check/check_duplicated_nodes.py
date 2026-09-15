# coding=utf-8
import traceback

import maya.cmds as cmds
import maya.utils as utils

from publish_components.utils.maya_utils.animation_checks import duplicated_cache_nodes


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None) -> str | None:
    """检查 |lay|cache_grp 下同父级、忽略 namespace 后重名的非引用物体。"""
    try:
        duplicates = utils.executeInMainThreadWithResult(duplicated_cache_nodes)
        if duplicates:
            return '以下物体重名，会影响缓存导出:\n' + '\n'.join(
                path for paths in duplicates.values() for path in paths)
    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None) -> str | None:
    """重新扫描重名物体并添加编号，保留 namespace。"""
    try:
        def repair() -> None:
            """在 Maya 主线程中修复重名，避免占用同级已有短名。"""
            duplicates = duplicated_cache_nodes()
            for (short_name, parent), paths in sorted(duplicates.items(), key=lambda item: len(item[0][1]), reverse=True):
                used = {node.rsplit('|', 1)[-1].rsplit(':', 1)[-1]
                        for node in cmds.listRelatives(parent, children=True, fullPath=True) or []}
                index = 1
                for path in paths:
                    while '{}_rn{}'.format(short_name, index) in used:
                        index += 1
                    new_short = '{}_rn{}'.format(short_name, index)
                    leaf = path.rsplit('|', 1)[-1]
                    namespace = leaf.rsplit(':', 1)[0] + ':' if ':' in leaf else ''
                    cmds.rename(path, ':' + namespace + new_short)
                    used.add(new_short)
                    index += 1
        utils.executeInMainThreadWithResult(repair)
    except Exception:
        return traceback.format_exc()
