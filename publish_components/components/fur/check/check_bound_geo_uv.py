# -*- coding: utf-8 -*-
import traceback
import maya.api.OpenMaya as om

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 XGen 生长面的 UV 是否全部位于 0-1 第一象限。"""
    try:
        def get_uvs(mesh_shape):
            selection=om.MSelectionList()
            selection.add(mesh_shape)
            dag_path=selection.getDagPath(0)
            mesh_fn=om.MFnMesh(dag_path)
            return mesh_fn.getUVs()

        bound_geometry=process_data.get("xgen_bound_geometry",[])
        bound_geometry_shapes=process_data.get("xgen_bound_geometry_shapes",{})

        if not bound_geometry:
            return u"没有获取到 XGen 生长面信息"
        if not bound_geometry_shapes:
            return u"没有获取到 XGen 生长面 Shape 信息"

        error_list=[]
        for bound_geo in bound_geometry:
            mesh_shape=bound_geometry_shapes.get(bound_geo)
            if not mesh_shape:
                error_list.append(u"{} 没有找到对应的 Mesh Shape".format(bound_geo))
                continue

            try:
                u_values,v_values=get_uvs(mesh_shape)
            except Exception:
                error_list.append(u"{} 无法读取 UV".format(bound_geo))
                continue

            if not u_values or not v_values:
                error_list.append(u"{} 没有 UV".format(bound_geo))
                continue

            if max(u_values)>1 or max(v_values)>1 or min(u_values)<0 or min(v_values)<0:
                error_list.append(u"{} 的 UV 超出 0-1 第一象限".format(bound_geo))

        if error_list:
            return "\n".join(error_list)

        if logger:
            logger.info(u"XGen 生长面 UV 检查通过，共检查 {} 个生长面".format(len(bound_geometry)))
    except Exception:
        return traceback.format_exc()