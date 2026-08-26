#!/usr/bin/env python  
# -*- coding:utf-8 -*-

error_name_list = []
import traceback
from publish_components.utils.sg_helper import check_is_internal_rig


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查控制器名称，内部绑定应该都以_ctrl或_CTL结尾
    """
    import maya.cmds as mc

    def run_check():
        global error_name_list
        error_name_list = []

        try:
            if mc.objExists('Root_grp.cocoVersion'):
                return ''

            task_id = process_data.get("task_id")
            if process_data.get("is_internal_rig") is None:
                process_data.update({"is_internal_rig":check_is_internal_rig(task_id)})
            if not process_data["is_internal_rig"]:
                return ''

            all_possible_ctrls = collect_all_possible_ctrls(exclude_crvs=['ctrlBox'])
            for node in all_possible_ctrls:
                if node.endswith('_ctrl') or node.endswith('_CTL'):
                    continue

                if not is_node_vis(node):
                    continue

                if not is_node_normally_overrided(node):
                    continue

                # coco rig special visbility control
                if node == 'Visibility':
                    continue

                error_name_list.append(node)

            mc.select(error_name_list)
            if error_name_list:
                logger.warning(u'以下物体应该为控制器，但没有以_ctrl结尾: \n{}'.format('\n'.join(error_name_list)))
                return u'以下物体应该为控制器，但没有以_ctrl结尾: \n{}'.format('\n'.join(error_name_list))

            logger.info('[CHECK DONE] check_ctrl_name')
            return ""
        except:
            return traceback.format_exc()

    def run_fix():
        '''Auto Fix'''
        for node in error_name_list:
            mc.rename(node, node + '_ctrl')
        return

    def collect_all_possible_ctrls(exclude_crvs=None):
        ctrl_list = []
        for crv in mc.ls(type='nurbsCurve'):
            if not mc.listConnections(crv, d=0):
                trans = mc.listRelatives(crv, p=1)[0]

                if exclude_crvs:
                    if trans in exclude_crvs:
                        continue

                is_ctrl = True
                for attr in ['t', 'r', 's', 'tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
                    if mc.listConnections(trans + '.' + attr, d=0):
                        is_ctrl = False
                if is_ctrl and trans not in ctrl_list:
                    ctrl_list.append(trans)
                dynamic_attrs = mc.listAttr(trans, userDefined=1)
                if dynamic_attrs:
                    for attr in dynamic_attrs:
                        if mc.listConnections(trans + '.' + attr, s=0) and trans not in ctrl_list:
                            ctrl_list.append(trans)
                            break
        return ctrl_list

    def is_node_vis(node):
        if mc.objectType(node) == 'transform':
            shapes = mc.listRelatives(node, s=1)
            if not shapes:
                return False
            node = shapes[0]

        vis = True
        full_path = mc.ls(node, long=1)[0]
        tokens = full_path.split('|')
        print(tokens)
        for i in range(len(tokens)):
            path = '|'.join(tokens[:i + 1])
            if path:
                if not mc.getAttr(path + '.visibility') and not mc.listConnections(path + '.visibility'):
                    vis = False
        return vis

    def is_node_normally_overrided(node):
        if mc.objectType(node) == 'transform':
            shapes = mc.listRelatives(node, s=1)
            if not shapes:
                return False
            node = shapes[0]

        normal = True
        full_path = mc.ls(node, long=1)[0]
        tokens = full_path.split('|')
        for i in range(len(tokens)):
            path = '|'.join(tokens[:i + 1])
            if path:
                if (mc.getAttr(path + '.template') and not mc.listConnections(path + '.template')) or \
                        (mc.getAttr(path + '.overrideEnabled') and mc.getAttr(
                            path + '.overrideDisplayType') != 0 and not mc.listConnections(
                            path + '.overrideDisplayType')):
                    normal = False
        return normal

    check_result = run_check()
    if check_result:
        run_fix()
