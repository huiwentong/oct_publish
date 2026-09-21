# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen 生长面及 Hair_xgenBaseGeo 组的 Transform 是否归零。"""
    try:
        def check_transform(node,node_name):
            if not cmds.objExists(node):
                raise RuntimeError(u"没有找到 {}".format(node_name))

            trans=cmds.getAttr(node+".translate")[0]
            if trans[0]!=0 or trans[1]!=0 or trans[2]!=0:
                raise RuntimeError(u"{}位移不为0, 请检查".format(node_name))

            rot=cmds.getAttr(node+".rotate")[0]
            if rot[0]!=0 or rot[1]!=0 or rot[2]!=0:
                raise RuntimeError(u"{}旋转不为0, 请检查".format(node_name))

            scale=cmds.getAttr(node+".scale")[0]
            if scale[0]!=1 or scale[1]!=1 or scale[2]!=1:
                raise RuntimeError(u"{}缩放不为1, 请检查".format(node_name))

        bound_geometry=process_data.get("xgen_bound_geometry",[])
        if not bound_geometry:
            raise RuntimeError(u"没有获取到 XGen 生长面信息")

        for bound_geo in bound_geometry:
            check_transform(bound_geo,u"生长面 {}".format(bound_geo))

        check_transform("|Root_grp|Hair_cfx|Hair_xgenBaseGeo",u"Hair_xgenBaseGeo组")

        if logger:
            logger.info(u"XGen 生长面及 Hair_xgenBaseGeo Transform 检查通过")
    except Exception:
        return traceback.format_exc()