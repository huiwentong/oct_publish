# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 Fur Publish 所需的 Hair_cfx 核心层级。"""
    try:
        fur_hierarchy=[
            "|Root_grp|Hair_cfx",
            "|Root_grp|Hair_cfx|Hair_curves",
            "|Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx",
            "|Root_grp|Hair_cfx|Hair_xgenBaseGeo",
        ]

        errors=[]
        for path in fur_hierarchy:
            if not cmds.objExists(path):
                errors.append(u"不存在节点：{}".format(path))
                continue
            if cmds.nodeType(path)!="transform":
                errors.append(u"节点不是 transform：{}".format(path))

        if errors:
            raise RuntimeError("\n".join(errors))

        if logger:
            logger.info(u"Fur 核心层级检查通过")
    except Exception:
        return traceback.format_exc()

def fix(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """创建缺失的 Fur 核心层级节点。"""
    try:
        fur_hierarchy=[
            "|Root_grp|Hair_cfx",
            "|Root_grp|Hair_cfx|Hair_curves",
            "|Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx",
            "|Root_grp|Hair_cfx|Hair_xgenBaseGeo",
        ]

        if not cmds.objExists("|Root_grp"):
            raise RuntimeError(u"不存在 Root_grp，无法自动修复 Fur 层级")

        for path in fur_hierarchy:
            if cmds.objExists(path):
                continue

            parent_path,name=path.rsplit("|",1)
            if not cmds.objExists(parent_path):
                raise RuntimeError(u"缺少父节点，无法创建 {}：{}".format(path,parent_path))

            cmds.createNode("transform",name=name,parent=parent_path)
            if logger:
                logger.warning(u"AUTO FIX: 创建节点 {}".format(path))

        if logger:
            logger.info(u"Fur 核心层级修复完成")
    except Exception:
        return traceback.format_exc()