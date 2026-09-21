# -*- coding: utf-8 -*-
import traceback
import maya.cmds as cmds

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen 生长面是否正确设置包裹。"""
    try:
        bound_geometry=process_data.get("xgen_bound_geometry",[])
        bound_geometry_shapes=process_data.get("xgen_bound_geometry_shapes",{})

        if not bound_geometry:
            raise RuntimeError(u"没有获取到 XGen 生长面信息")

        errors=[]
        for bound_geo in bound_geometry:
            shape=bound_geometry_shapes.get(bound_geo)
            if not shape:
                errors.append(u"生长面 {} 没有获取到 Mesh Shape".format(bound_geo))
                continue
            if not cmds.connectionInfo(shape+".inMesh",isDestination=True):
                errors.append(u"生长面 {} 没有设置包裹".format(bound_geo))

        if errors:
            raise RuntimeError("\n".join(errors))

        if logger:
            logger.info(u"XGen 生长面包裹检查通过")
    except Exception:
        return traceback.format_exc()