# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查几何体的位移旋转为0， 放缩为1
    """
    try:
        def check():
            n_root = process_data.get('root', '|Root_grp')
            n_root = pm.PyNode(n_root)
            all_transforms = pm.listRelatives(n_root, ad=True, type='transform', path=True)
            all_transforms.append(n_root)
            err_nodes = []
            for tans_node in all_transforms:
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                    if abs(tans_node.getAttr(attr)) > 0.000001:
                        err_nodes.append(tans_node)

                for attr in ['sx', 'sy', 'sz']:
                    if abs(tans_node.getAttr(attr) - 1.0) > 0.000001:
                        err_nodes.append(tans_node)
            return err_nodes

        error_nodes = utils.executeInMainThreadWithResult(check)
        if len(error_nodes) > 0:
            process_data["untouched_transforms_error_nodes"] = error_nodes
            msg = "以下几何体的位移旋转不为0， 放缩不为1：\n{}".format("\n".join([n.nodeName() for n in error_nodes]))
            return msg

    except:
        return traceback.format_exc()

def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    try:
        def _fix():
            fal_nodes = []
            error_nodes = process_data.get('untouched_transforms_error_nodes', [])
            for t_n in error_nodes:
                for atr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                    try:
                        logger.warning("AUTO FIX: 自动修复节点‘{}’的‘{}’值为0.0！".format(t_n.nodeName(), atr))
                        t_n.setAttr(atr, lock=False)
                        t_n.setAttr(atr, 0.0)
                    except:
                        fal_nodes.append(t_n.nodeName())
                        logger.error("自动修复节点‘{}’失败！因为：\n{}".format(t_n.nodeName(), traceback.format_exc()))

                for atr in ['sx', 'sy', 'sz']:
                    try:
                        logger.warning("AUTO FIX: 自动修复节点‘{}’的‘{}’值为1.0！".format(t_n.nodeName(), atr))
                        t_n.setAttr(atr, lock=False)
                        t_n.setAttr(atr, 1.0)
                    except:
                        fal_nodes.append(t_n.nodeName())
                        logger.error("自动修复节点‘{}’失败！因为：\n{}".format(t_n.nodeName(), traceback.format_exc()))
            return fal_nodes

        failed_nodes = utils.executeInMainThreadWithResult(_fix)
        if failed_nodes:
            msg = "这些节点自动修复 位移 旋转 放缩 失败, 请手动修复！：{}".format("\n".join(failed_nodes))
            logger.error(msg)
            return msg
    except:
        return traceback.format_exc()


