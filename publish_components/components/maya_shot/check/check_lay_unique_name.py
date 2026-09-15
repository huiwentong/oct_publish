# -*- coding: utf-8 -*-
import re
import traceback

import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查 |lay|cache_grp 层级下是否有重复名称的节点
    """
    # 去掉 namespace 和数字后缀后按前缀分组，同组内短名重复即报错，Fix 会按 前缀+序号 重命名。
    try:
        def find_duplicates():
            """返回 {前缀: [PyNode, ...]}，只包含真的有重名的组"""
            duplicates = {}
            if not pm.objExists('|lay|cache_grp'):
                return duplicates
            all_transform_node = pm.listRelatives('|lay|cache_grp', ad=True, type='transform')
            if not all_transform_node:
                return duplicates

            groups = {}
            for node in all_transform_node:
                real_name = node.shortName().split(':')[-1]
                match = re.match(r'([\w]+?)(\d+)$', real_name)
                if match:
                    real_name = match.group(1)
                groups.setdefault(real_name, []).append(node)

            for real_name, nodes in groups.items():
                if len(nodes) < 2:
                    continue
                name_list = [n.shortName().split(':')[-1] for n in nodes]
                if len(name_list) != len(set(name_list)):
                    duplicates[real_name] = nodes
            return duplicates

        duplicates = utils.executeInMainThreadWithResult(find_duplicates)
        if duplicates:
            return u"|lay|cache_grp 下有重名节点，请点击 Fix 自动重命名：{0}".format(
                ', '.join(sorted(duplicates.keys())))
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """按 前缀+序号 重命名 cache_grp 下的重名节点"""
    try:
        def unique_rename(real_name, nodes):
            exists_name_list = [n.shortName().split(':')[-1] for n in nodes]

            number_list = []
            for name in exists_name_list:
                match = re.match(r'([\w]+?)(\d+)$', name)
                if match:
                    number_list.append(int(match.group(2)))
            suffix_number = max(number_list) + 1 if number_list else 1

            for node in nodes:
                # 只处理真正重名的节点
                if exists_name_list.count(node.shortName().split(':')[-1]) < 2:
                    continue
                with_number_name = real_name + str(suffix_number)
                if ':' in node.shortName():
                    new_name = node.shortName().rsplit(':', 1)[0] + ':' + with_number_name
                else:
                    new_name = with_number_name
                suffix_number += 1
                old_name = node.shortName()
                node.rename(new_name)
                logger.info(u"AUTO FIX: rename {0} -> {1}".format(old_name, new_name))

        def repair():
            if not pm.objExists('|lay|cache_grp'):
                return
            all_transform_node = pm.listRelatives('|lay|cache_grp', ad=True, type='transform') or []
            groups = {}
            for node in all_transform_node:
                real_name = node.shortName().split(':')[-1]
                match = re.match(r'([\w]+?)(\d+)$', real_name)
                if match:
                    real_name = match.group(1)
                groups.setdefault(real_name, []).append(node)

            for real_name, nodes in groups.items():
                if len(nodes) < 2:
                    continue
                name_list = [n.shortName().split(':')[-1] for n in nodes]
                if len(name_list) != len(set(name_list)):
                    unique_rename(real_name, nodes)

        utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
