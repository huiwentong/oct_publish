# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils
import pymel.core as pm


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查贴图色彩空间
    """
    # 根据项目的色彩管理，检查贴图节点的 colorSpace 是否是 OCIO 配置里的合法输入空间。
    #
    # 没有复用 tex/check_colorspace：那个组件的白名单只有 Utility - sRGB - Texture 和
    # Utility - Raw 两个值，其余合法色彩空间一律判为“无法自动修复”。ASB 拆分场景是
    # 引用一堆子资产拼起来的，贴图色彩空间不由拆分环节的人控制，这里按 OCIO 的全量
    # inputSpaceNames 放行，与老 publish_tool 的判定保持一致。
    try:
        def check():
            # 能自动修复的错误写法 -> 修正后的值
            fix_map = {"sRGB": "Utility - sRGB - Texture", "Raw": "Utility - Raw"}

            cm_enabled = cmds.colorManagementPrefs(query=True, cmEnabled=True)
            if cm_enabled:
                valid_spaces = cmds.colorManagementPrefs(query=True, inputSpaceNames=True)
            else:
                valid_spaces = ["sRGB", "Raw"]

            fix_data = {}
            unknown = []
            for node in pm.ls(type=["file", "aiImage"]):
                color_space = node.getAttr("colorSpace")
                if color_space in valid_spaces:
                    continue

                fix_cs = fix_map.get(color_space)
                if fix_cs:
                    fix_data[node.name()] = fix_cs
                else:
                    unknown.append("{0} --> {1}".format(node.name(), color_space))

            return cm_enabled, fix_data, unknown

        cm_enabled, fix_data, unknown = utils.executeInMainThreadWithResult(check)

        # 老流程在色彩管理没开时退回 sRGB/Raw 白名单继续检查，这里保持一致，
        # 只提示不拦截，避免环境没配好就卡住整条发布
        if not cm_enabled:
            logger.warning(u"当前场景没有开启色彩管理，已退回 sRGB / Raw 白名单做检查")

        process_data["color_space_error_nodes"] = fix_data

        errors = []
        if fix_data:
            errors.append(u"以下贴图节点色彩空间需要修复:\n{0}".format(
                "\n".join("{0} --> {1}".format(k, v) for k, v in fix_data.items())))
        if unknown:
            errors.append(u"以下贴图节点色彩空间不在色彩管理的输入空间列表内，无法自动修复:\n{0}".format(
                "\n".join(unknown)))
        if errors:
            return "\n\n".join(errors)

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    把能自动修复的贴图色彩空间改成正确值
    """
    try:
        def repair():
            fix_data = process_data.get("color_space_error_nodes", {})
            failed = []
            for node_name, color_space in fix_data.items():
                try:
                    pm.PyNode(node_name).setAttr("colorSpace", color_space)
                    logger.warning(u"AUTO FIX: 修改贴图的色彩空间: {0} -> {1}".format(
                        node_name, color_space))
                except Exception:
                    failed.append(node_name)
                    logger.error(u"修复贴图 {0} 的色彩空间失败: {1}".format(
                        node_name, traceback.format_exc()))
            return failed

        failed = utils.executeInMainThreadWithResult(repair)
        if failed:
            return u"以下贴图节点色彩空间自动修复失败:\n{0}".format("\n".join(failed))

    except Exception:
        return traceback.format_exc()
