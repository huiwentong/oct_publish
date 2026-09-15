# -*- coding: utf-8 -*-
import importlib
import traceback

import maya.cmds as cmds
import maya.utils as utils

from publish_components.utils.maya_utils import asb_build


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查场景中 mayaUsdProxyShape 对应的 USD 文件是否有未保存的修改
    """
    # init_usd 会加载 mayaUsdPlugin 并把 USD 编辑的保存策略设为“Maya 文件和 USD 文件分开保存”，
    # 避免保存时弹窗。
    #
    # mayaUsd.ufe 用 importlib 动态导入：组件顶层 import 会被提到 CLI 脚本最前面，
    # 那时 mayaUsdPlugin 还没加载，直接写 import mayaUsd 会失败。
    try:
        def check():
            asb_build.init_usd()
            maya_usd_ufe = importlib.import_module('mayaUsd.ufe')
            dirty_list = []
            for proxy in cmds.ls(type='mayaUsdProxyShape', long=True) or []:
                stage = maya_usd_ufe.getStage(proxy)
                if stage and stage.GetRootLayer().dirty:
                    dirty_list.append(proxy)
            return dirty_list

        dirty_list = utils.executeInMainThreadWithResult(check)
        if dirty_list:
            return u"以下 USD 节点对应的文件未保存，请点击 Fix 保存:\n{0}".format('\n'.join(dirty_list))
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """保存所有 mayaUsdProxyShape 的 root layer"""
    try:
        def repair():
            asb_build.init_usd()
            maya_usd_ufe = importlib.import_module('mayaUsd.ufe')
            for proxy in cmds.ls(type='mayaUsdProxyShape', long=True) or []:
                stage = maya_usd_ufe.getStage(proxy)
                if not stage:
                    continue
                layer = stage.GetRootLayer()
                if layer.anonymous:
                    return u"USD Layer 尚未另存为文件，无法自动保存: {0}".format(proxy)
                if layer.dirty and not layer.Save():
                    return u"USD Layer 保存失败: {0}".format(proxy)
                logger.info(u"AUTO FIX: 已保存 USD {0}".format(layer.identifier))
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
