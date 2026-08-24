# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.OpenMaya as om

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查四边面
    """
    try:
        l_invalid_meshes = []
        l_invalid_faces = []
        n_geo = process_data.get('geo', '|Root_grp|Geo_grp')
        n_geo = pm.PyNode(n_geo)

        l_meshes = pm.listRelatives(n_geo, ad=True, type='mesh', path=True) or []
        for mesh_node in l_meshes:
            sl = om.MSelectionList()
            sl.add(mesh_node.fullPath())
            mesh_dag = om.MDagPath()
            sl.getDagPath(0, mesh_dag)
            mesh_mfn = om.MFnMesh(mesh_dag)

            for i in range(mesh_mfn.numPolygons()):
                if mesh_mfn.polygonVertexCount(i) > 4:
                    l_invalid_meshes.append(str(mesh_node))
                    l_invalid_faces.append(str(mesh_node + '.f[' + str(i) + ']'))

        l_invalid_meshes = list(set(l_invalid_meshes))

        if len(l_invalid_meshes) > 0:
            pm.select(l_invalid_faces, r=True)
            return u'有些polygon几何体有多于4条棱的面:\n' + ', '.join(l_invalid_meshes)

    except:
        return traceback.format_exc()