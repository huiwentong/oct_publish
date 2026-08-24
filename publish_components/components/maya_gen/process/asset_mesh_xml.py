# -*- coding: utf-8 -*-
import traceback, os
import hashlib
from xml.dom.minidom import Document
import pymel.core as pm
import maya.api.OpenMaya as om
import maya.utils as utils
def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """将模型 high 组下的mesh层级结构，名称，点线面数记录为下游组比对做准备。"""

    try:
        doc = Document()
        def create_structure(root_elem, root_node):
            if pm.objExists(root_node):
                for node in pm.listRelatives(root_node):
                    if node.type() == 'transform':
                        trans = doc.createElement('transform')
                        trans.setAttribute('name', node.fullPath())
                        root_elem.appendChild(trans)
                        create_structure(trans, node)
                    elif node.type() == 'mesh' and (not node.isIntermediate()):
                        if pm.polyEvaluate(node, face=True) == 0:
                            # ensure bytes for py3
                            topology = hashlib.md5(b' ').hexdigest()
                        else:
                            sl = om.MSelectionList()
                            sl.add(node.fullPath())
                            mesh_dag = sl.getDagPath(0)
                            mesh_mfn = om.MFnMesh(mesh_dag)
                            v = mesh_mfn.getVertices()
                            v_str0 = '[' + ', '.join([str(i) for i in v[0]]) + ']'
                            v_str1 = '[' + ', '.join([str(i) for i in v[1]]) + ']'
                            v_str = v_str0 + ' ' + v_str1

                            # Compatible with python 2 and 3
                            try:
                                topology = hashlib.md5(v_str).hexdigest()
                            except TypeError:
                                topology = hashlib.md5(v_str.encode('utf-8')).hexdigest()

                        mesh = doc.createElement('mesh')
                        mesh.setAttribute('name', node.fullPath())
                        mesh.setAttribute('vertex', str(pm.polyEvaluate(node, vertex=True)))
                        mesh.setAttribute('edge', str(pm.polyEvaluate(node, edge=True)))
                        mesh.setAttribute('face', str(pm.polyEvaluate(node, face=True)))
                        mesh.setAttribute('topology', topology)
                        root_elem.appendChild(mesh)

        def process():
            version_dir = process_data["version_dir"]
            n_root = pm.PyNode(process_data.get('root', '|Root_grp'))
            n_geo = pm.PyNode(process_data.get('geo', '|Root_grp|Geo_grp'))
            n_high = pm.PyNode(process_data.get('high', '|Root_grp|Geo_grp|high'))

            mesh_xml = version_dir + '/mesh.xml'
            master = doc.createElement('transform')
            master.setAttribute('name', n_root.fullPath())
            doc.appendChild(master)
            poly = doc.createElement('transform')
            poly.setAttribute('name', n_geo.fullPath())
            master.appendChild(poly)
            if pm.objExists(n_high):
                res_node = doc.createElement('transform')
                res_node.setAttribute('name', n_high.fullPath())
                poly.appendChild(res_node)
                create_structure(res_node, n_high.fullPath())

            with open(mesh_xml, 'w') as f:
                f.write(doc.toprettyxml(indent='    '))

        process()

    except Exception:
        return traceback.format_exc()
