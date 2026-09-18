# -*- coding: utf-8 -*-

import traceback
import maya.cmds as cmds


FUR_HIERARCHY = [
    '|Root_grp|Hair_cfx',
    '|Root_grp|Hair_cfx|Hair_curves',
    '|Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx',
    '|Root_grp|Hair_cfx|Hair_xgenBaseGeo',
]


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Fur Publish 所需的 Hair_cfx 核心层级。"""
    try:
        error_list = []

        for path in FUR_HIERARCHY:
            if not cmds.objExists(path):
                error_list.append(u'不存在节点：{}'.format(path))
                continue

            try:
                if cmds.nodeType(path) != 'transform':
                    error_list.append(u'节点不是 transform：{}'.format(path))
            except Exception:
                error_list.append(u'无法读取节点类型：{}'.format(path))

        if error_list:
            return '\n'.join(error_list)

        return ""

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """创建缺失的 Fur 核心层级节点。"""
    try:
        if not cmds.objExists('|Root_grp'):
            return u'不存在 Root_grp，无法自动修复 Fur 层级'

        for path in FUR_HIERARCHY:
            if cmds.objExists(path):
                continue

            parent_path, name = path.rsplit('|', 1)

            if not cmds.objExists(parent_path):
                return u'缺少父节点，无法创建 {}：{}'.format(path, parent_path)

            cmds.createNode('transform', name=name, parent=parent_path)

            if logger:
                logger.warning(u'AUTO FIX: 创建节点 {}'.format(path))

        return ""

    except Exception:
        return traceback.format_exc()