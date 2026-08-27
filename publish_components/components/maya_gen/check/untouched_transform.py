# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查几何体的位移旋转为0， 放缩为1
    """
    try:
        n_root = process_data.get('root', '|Root_grp')
        n_root = pm.PyNode(n_root)
        all_transforms = pm.listRelatives(n_root, ad=True, type='transform', path=True)
        all_transforms.append(n_root)

        error_nodes = []
        for tans_node in all_transforms:
            tans_node = pm.PyNode(tans_node)
            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                if abs(tans_node.getAttr(attr)) > 0.000001:
                    try:
                        logger.warning("AUTO FIX: 自动修复节点‘{}’的‘{}’值为0.0！".format(tans_node.nodeName(), attr))
                        tans_node.setAttr(attr, lock=False)
                        tans_node.setAttr(attr, 0.0)
                    except:
                        error_nodes.append(tans_node.nodeName())
                        pass

            for attr in ['sx', 'sy', 'sz']:
                if abs(tans_node.getAttr(attr) - 1.0) > 0.000001:
                    try:
                        logger.warning("AUTO FIX: 自动修复节点‘{}’的‘{}’值为1.0！".format(tans_node.nodeName(), attr))
                        tans_node.setAttr(attr, lock=False)
                        tans_node.setAttr(attr, 1.0)
                    except:
                        error_nodes.append(tans_node.nodeName())
                        pass

        if error_nodes:
            return "这些节点的位移，旋转不是 0， 缩放不是 1, 自动修复失败：{}".format("\n".join(error_nodes))
    except:
        return traceback.format_exc()


