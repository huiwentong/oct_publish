# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """清除transform节点的链接输入, 显示并解锁"""
    try:
        TR_ATTRS = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY',
                    'scaleZ', 'visibility']

        root = process_data.get("root", "|Root_grp")
        for node in pm.listRelatives(root, ad=True, type='transform'):
            if node.type() == 'instancer':
                continue
            if pm.listConnections(node, s=1, d=0):
                logger.warning("AUTO FIX：节点 '{}' 有属性被其他节点链接, 开始断开！".format(str(node)))
                for con_pair in pm.listConnections(node, s=1, d=0, c=1, plugs=1):
                    pm.disconnectAttr(con_pair[1], con_pair[0])

            logger.warning("AUTO FIX：显示并解锁节点 '{}'".format(node))
            for attr in TR_ATTRS:
                if not pm.getAttr(node.name() + '.' + attr, keyable=True) or pm.getAttr(node.name() + '.' + attr, lock=True):
                    pm.setAttr(node.name() + '.' + attr, keyable=1)
                    pm.setAttr(node.name() + '.' + attr, lock=0)

    except Exception:
        return traceback.format_exc()
