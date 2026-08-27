#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import traceback
from publish_components.utils.sg_helper import check_is_internal_rig
import maya.cmds as mc
import maya.utils as utils

error_value_list = []
error_connection_list = []


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查控制器数值以及是否连接输入
    """

    def get_all_ctrls(only_ctrl_itself=False, full_path=False):
        ctrl_list = mc.ls('*_ctrl', long=full_path)
        ctrl_list.extend(mc.ls('*_CTL', long=full_path))
        if only_ctrl_itself:
            ctrl_list = [ctrl for ctrl in ctrl_list if
                         not ctrl.endswith('_pri_ctrl') and not ctrl.endswith('_sec_ctrl')]
        return ctrl_list

    def process():
        global error_value_list, error_connection_list
        error_value_list = []
        error_connection_list = []
        try:
            task_id = process_data.get("task_id")
            if process_data.get("is_internal_rig") is None:
                process_data.update({"is_internal_rig": check_is_internal_rig(task_id)})
            if not process_data["is_internal_rig"]:
                return ''

            for ctrl in get_all_ctrls():
                attrs_list = mc.listAttr(ctrl, keyable=True, shortNames=True)
                if attrs_list:
                    for attr in attrs_list:
                        if mc.getAttr(ctrl + '.' + attr, lock=1):
                            continue
                        if attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                            if round(mc.getAttr(ctrl + '.' + attr), 5) != 0 and ctrl not in error_value_list:
                                error_value_list.append(ctrl)
                        elif attr in ['sx', 'sy', 'sz']:
                            if round(mc.getAttr(ctrl + '.' + attr), 5) != 1 and ctrl not in error_value_list:
                                error_value_list.append(ctrl)

                        if mc.listConnections(ctrl + '.' + attr, s=1, d=0, skipConversionNodes=True):
                            error_connection_list.append(ctrl)

            if len(error_connection_list):
                mc.select(error_connection_list)
                logger.warning(u'存在错误链接的控制器: \n {}'.format('\n'.join(error_connection_list)))
                return u'存在错误链接的控制器: \n {}'.format('\n'.join(error_connection_list))

            if len(error_value_list):
                mc.select(error_value_list)
                logger.warning(u'存在默认数值错误控制器: \n {}'.format('\n'.join(error_value_list)))
                return u'存在默认数值错误控制器: \n {}'.format('\n'.join(error_value_list))

            return ''

        except:
            return traceback.format_exc()

    def run_fix():
        '''Auto Fix'''
        warning_str = u'自动修复可能会断开连接，重置数值，影响绑定效果，请确认之后再自动修复，修复后再检查效果。 \n'
        warning_str += u'\t是否继续?'
        result = mc.confirmDialog(title='Warning', message=warning_str, button=[u'继续', u'取消'],
                                  defaultButton=u'继续', cancelButton=u'取消')

        if result == u'继续':
            logger.info(u"Auto Fix: 修复控制器的 Keyable 的 Translate Rotate Scale 到默认值；修复 Keyable 属性到无链接")
            if error_connection_list:
                for ctrl in error_connection_list:
                    con_list = mc.listConnections(ctrl, s=1, d=0, skipConversionNodes=True, connections=True)
                    for source, dest in con_list:
                        mc.discnnectAttrs(source, dest)

            if error_value_list:
                for ctrl in error_value_list:
                    attrs_list = mc.listAttr(ctrl, keyable=True, shortNames=True)
                    if attrs_list:
                        for attr in attrs_list:
                            if attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                                mc.setAttr(ctrl + '.' + attr, 0)
                            elif attr in ['sx', 'sy', 'sz']:
                                mc.setAttr(ctrl + '.' + attr, 1)

    return utils.executeInMainThreadWithResult(process)
