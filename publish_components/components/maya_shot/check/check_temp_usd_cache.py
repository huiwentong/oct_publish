# coding=utf-8
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None) -> str | None:
    """检查场景内的临时 USD 缓存（名字包含 _low_ani）。"""
    try:
        nodes = utils.executeInMainThreadWithResult(
            lambda: [node for node in cmds.ls(type='mayaUsdProxyShape', long=True) or []
                     if '_low_ani' in node.rsplit('|', 1)[-1]])
        if nodes:
            return '场景中有临时 USD 缓存，请点击 Fix 删除或手动处理:\n' + '\n'.join(nodes)
    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None) -> str | None:
    """重新查找临时缓存，删除其父节点，与旧发布修复行为一致。"""
    try:
        def repair() -> None:
            """在 Maya 主线程内删除临时缓存父节点。"""
            parents = set()
            for node in cmds.ls(type='mayaUsdProxyShape', long=True) or []:
                if '_low_ani' in node.rsplit('|', 1)[-1]:
                    parents.update(cmds.listRelatives(node, parent=True, fullPath=True) or [])
            for node in sorted(parents, key=len, reverse=True):
                if cmds.objExists(node):
                    cmds.delete(node)
        utils.executeInMainThreadWithResult(repair)
    except Exception:
        return traceback.format_exc()
