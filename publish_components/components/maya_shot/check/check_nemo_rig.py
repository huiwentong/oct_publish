# -*- coding: utf-8 -*-
import os
import re
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct_maya.utils.maya_utils.pipe import list_ref_node


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    Nemo 绑定要切回正常 rig 再发布下游，否则无法正常渲染
    """
    # 老 maya/nemo_to_maya_rig
    try:
        def check():
            asset_to_switch = []
            for ref in list_ref_node():
                ref_file = cmds.referenceQuery(ref, filename=True)
                if 'rigging_nemo' in ref_file:
                    asset_to_switch.append(ref)
            return asset_to_switch

        asset_to_switch = utils.executeInMainThreadWithResult(check)
        if asset_to_switch:
            return u"不应该使用 NemoRig 发布，请切回正常 RIG 确认效果后再发布（可点击 Fix 自动切换）:\n" + \
                   '\n'.join(asset_to_switch)
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """把 rigging_nemo 的引用切回 rigging 的绑定文件"""
    try:
        def repair():
            not_found = []
            for ref in list_ref_node():
                ref_file = cmds.referenceQuery(ref, filename=True)
                if 'rigging_nemo' not in ref_file:
                    continue
                ref_file = re.sub(r"\{\d+\}$", "", ref_file)
                maya_rig = ref_file.replace('rigging_nemo_low', 'rigging').replace('rigging_nemo', 'rigging')
                if os.path.isfile(maya_rig):
                    cmds.file(maya_rig, loadReference=ref)
                    logger.info(u"AUTO FIX: {0} 切换到 {1}".format(ref, maya_rig))
                else:
                    not_found.append(maya_rig)
            if not_found:
                return u"找不到对应的正常绑定文件，请手动切换:\n" + '\n'.join(not_found)
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
