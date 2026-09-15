# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils

from oct_maya.utils.maya_utils import pipe


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    Component 的 Root 节点下不应该存在非 reference 本身的节点
    """
    # Reference / Asb 资产的 high 组下如果混进了场景里自己建的节点（约束节点除外），
    # 会随缓存一起输出，这里逐个 component 检查并报出异常节点。
    try:
        def find_abnormal_nodes():
            error_node_list = []
            constraint_types = cmds.nodeType('constraint', derived=True, isTypeName=True)
            comp_info = pipe.ShotDataGenerator().generate_comp_info()
            for comp, info in comp_info.items():
                # asb 资产没有 high 层级
                if info['type'] == 'assembly':
                    continue
                high_grp = info['namespace'] + ':high'
                if not cmds.objExists(high_grp):
                    continue

                comp_node = info['component_node']
                if info['type'] == 'reference':
                    comp_node_list = cmds.referenceQuery(comp_node, nodes=True, dagPath=True)
                else:
                    comp_node_list = cmds.container(comp_node, q=True, nodeList=True)
                comp_node_list = [cmds.ls(node, long=True)[0] for node in comp_node_list]

                for node in cmds.listRelatives(high_grp, ad=True, type='transform', fullPath=True) or []:
                    if node in comp_node_list:
                        continue
                    if cmds.objectType(node) in constraint_types:
                        continue
                    error_node_list.append(node)

            if error_node_list:
                cmds.select(error_node_list)
            return error_node_list

        error_node_list = utils.executeInMainThreadWithResult(find_abnormal_nodes)
        # 存进 process_data 给 fix 用，main 和 fix 之间没有别的状态通道
        process_data['abnormal_dag_nodes'] = error_node_list
        if error_node_list:
            return u"Reference 或 Asb 资产下有非资产本身的节点，请删除或者移到 |lay|cache_grp 组（可点击 Fix 处理）\n" + \
                   '\n'.join(error_node_list)
    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """询问后把异常节点移到 |lay|cache_grp 或删除"""
    try:
        def repair():
            error_node_list = [n for n in process_data.get('abnormal_dag_nodes', []) if cmds.objExists(n)]
            if not error_node_list:
                return u"没有找到异常节点，请先重新运行检查"
            msg = u'Reference 或 Asb 资产下有非资产本身的节点，如何处理？\n\t{0}'.format(' '.join(error_node_list))
            result = cmds.confirmDialog(title='Warning', message=msg,
                                        button=[u'移到 cache_grp', u'删除', u'取消'],
                                        defaultButton=u'取消', cancelButton=u'取消', dismissString=u'取消')
            if result == u'移到 cache_grp':
                if not cmds.objExists('|lay'):
                    cmds.group(em=True, name='lay')
                if not cmds.objExists('|lay|cache_grp'):
                    cmds.group(em=True, name='cache_grp', parent='|lay')
                cmds.parent(error_node_list, '|lay|cache_grp')
                logger.info(u"AUTO FIX: 移到 |lay|cache_grp: {0}".format(' '.join(error_node_list)))
            elif result == u'删除':
                cmds.delete(error_node_list)
                logger.info(u"AUTO FIX: 删除 {0}".format(' '.join(error_node_list)))
            else:
                return u"已取消，异常节点未处理"
            return ""

        return utils.executeInMainThreadWithResult(repair)
    except:
        return traceback.format_exc()
