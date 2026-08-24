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
        n_root = process_data.get("root", pm.PyNode('|Root_grp'))
        n_geo = process_data.get("geo", pm.PyNode('|Root_grp|Geo_grp'))

        # Freeze transoform - 坐标清零
        pm.select(n_geo, r=True)
        utils.executeInMainThreadWithResult(lambda :pm.mel.eval('DeleteHistory;'))
        utils.executeInMainThreadWithResult(lambda :pm.select(cl=True))

        # Clean intermediate objects
        l_meshes = pm.listRelatives(n_root, ad=True, type='mesh', fullPath=True)
        for mesh_node in l_meshes:
            if mesh_node.isIntermediateObject():
                pm.delete(mesh_node)

        # No sibling mesh nodes
        l_render_nodes = pm.listRelatives(n_root, ad=True, type='mesh', fullPath=True)
        l_render_nodes.extend(pm.listRelatives(n_root, ad=True, type='nurbsCurve', fullPath=True))

        for render_node in l_render_nodes:
            trans_node = render_node.getParent()
            l_children = pm.listRelatives(trans_node, fullPath=True, type='mesh')
            l_children.extend(pm.listRelatives(trans_node, fullPath=True, type='nurbsCurve'))
            if len(l_children) > 1:
                return u'Transform节点 ' + trans_node.name() + u' 之下有多个mesh/curve节点。需要模型师手动找到并删除。（无法使用自动修复）'

    except:
        return traceback.format_exc()


