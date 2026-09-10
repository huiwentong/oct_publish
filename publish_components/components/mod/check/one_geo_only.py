# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查单个 mesh/curve，是否有intermediate object
    """
    #u"清除历史记录。一个transform下最多只能有一个 mesh/nurbsCurve节点。如果有intermediate object需要删除掉。"
    try:
        def check():
            n_root = process_data.get("root", '|Root_grp')
            n_geo = process_data.get("geo", '|Root_grp|Geo_grp')

            pm.select(n_geo, r=True)
            pm.mel.eval('DeleteHistory;')
            pm.select(cl=True)

            # Clean intermediate objects
            l_meshes = pm.listRelatives(n_root, ad=True, type='mesh', fullPath=True)
            for mesh_node in l_meshes:
                if mesh_node.isIntermediateObject():
                    pm.delete(mesh_node)

            # No sibling mesh nodes
            l_render_nodes = pm.listRelatives(n_root, ad=True, type='mesh', fullPath=True)
            l_render_nodes.extend(pm.listRelatives(n_root, ad=True, type='nurbsCurve', fullPath=True))

            er_nodes = []
            for render_node in l_render_nodes:
                trans_node = render_node.getParent()
                l_children = pm.listRelatives(trans_node, fullPath=True, type='mesh')
                l_children.extend(pm.listRelatives(trans_node, fullPath=True, type='nurbsCurve'))
                if len(l_children) > 1:
                    er_nodes.append(trans_node.name())
            return er_nodes

        error_node = utils.executeInMainThreadWithResult(check)
        if error_node:
            return "以下节点下有多个mesh/curve shape节点。需要模型师手动找到并删除：{}\n".format("\n".join(error_node))

    except:
        return traceback.format_exc()


