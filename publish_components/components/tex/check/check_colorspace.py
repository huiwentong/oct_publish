# -*- coding: utf-8 -*-
import traceback
import os
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查贴图色彩空间"""
    try:
        def check():
            color_map = {"sRGB": "Utility - sRGB - Texture", "Raw": "Utility - Raw"}
            ocio_f = pm.colorManagementPrefs(q=True, configFilePath=True)
            f_data = {}
            e_data = []

            for node in pm.ls(type=["file", "aiImage"]):
                color_space = node.getAttr("colorSpace")
                if color_space in color_map.values():
                    continue

                fix_cs = color_map.get(color_space)
                if fix_cs:
                    f_data[node.name()] = fix_cs
                else:
                    e_data.append(node.name())

            return ocio_f, f_data, e_data

        ocio_file, fix_data, unknown = utils.executeInMainThreadWithResult(check)

        if not os.path.isfile(ocio_file):
            return "当前场景没有配置 OCIO！！\n可以重新设置下任务环境，再提交！"

        process_data["color_space_error_nodes"] = fix_data
        errors = []

        if fix_data:
            errors.append("以下贴图节点色彩空间需要修复:\n{}".format( "\n".join(fix_data)))
        if unknown:
            errors.append("以下贴图节点无法自动修复:\n{}".format("\n".join(unknown)))
        if errors:
            return "\n\n".join(errors)

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        fix_data = process_data.get("color_space_error_nodes", {})

        def repair():
            for node, color_space in fix_data.items():
                pm.PyNode(node).setAttr("colorSpace", color_space)
                logger.warning("AUTO FIX: 修改贴图的色彩空间: {} -> {}".format(node, color_space))
        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
