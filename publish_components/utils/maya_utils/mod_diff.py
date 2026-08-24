# -*- coding:utf-8 -*-

from xml.etree import ElementTree
import hashlib

class Mod_Diff():
    
    def __init__(self):
        self.l_moved = []
        self.l_missing = []
        self.l_new = []
        self.l_topology_changed = []
        self.l_vtx_num = []
        self.l_wrong_order = []
        return

    def xml_to_dict(self, mesh_xml, root_node):
        d_meshes = {}
        l_order = []
        tree = ElementTree.parse(mesh_xml)
        root = tree.getroot()

        # Compatible with python 2 and 3
        if hasattr(root, 'iter'):
            l_meshes = root.iter("mesh")
        else:
            l_meshes = root.getiterator("mesh")

        for mesh in l_meshes:
            full_path = mesh.attrib['name']
            if not root_node in full_path:
                continue
            mesh_name = full_path.split('|')[-1]
            topology = mesh.attrib['topology']
            vertex = mesh.attrib['vertex']
            d_meshes[mesh_name] = {'path': full_path, 'topology': topology, 'vertex': vertex}
            l_order.append(mesh_name)
        return d_meshes, l_order


    def parse_xml(self, mesh_xml, root_node):
        import pymel.core as pm
        import maya.api.OpenMaya as om

        d_old_meshes, l_old_order = self.xml_to_dict(mesh_xml, root_node)

        d_new_meshes = {}
        l_new_mesh = pm.listRelatives(root_node, ad=True, type='mesh', noIntermediate=True)
        for i, mesh in enumerate(l_new_mesh):
            mesh_name = mesh.name().split('|')[-1]
            d_new_meshes[mesh_name] = ''
            if not mesh_name in d_old_meshes:
                self.l_new.append(mesh_name)
            else:
                full_path = mesh.fullPath()

                if full_path != d_old_meshes[mesh_name]['path']:
                    self.l_moved.append(mesh_name)

                sl = om.MSelectionList()
                sl.add(full_path)
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

                if topology != d_old_meshes[mesh_name]['topology']:
                    self.l_topology_changed.append(mesh_name)
                elif pm.polyEvaluate(mesh, v=True) != int(d_old_meshes[mesh_name]['vertex']):
                    self.l_vtx_num.append(mesh_name)

        for mesh_name in d_old_meshes.keys():   
            if not mesh_name in d_new_meshes:
                self.l_missing.append(mesh_name)

        if len(d_old_meshes.keys()) == len(l_new_mesh):
            for i, mesh  in enumerate(l_new_mesh):
                mesh_name = mesh.name().split('|')[-1]
                #print(mesh_name, l_old_order[i])
                if mesh_name != l_old_order[i]:
                    self.l_wrong_order.append(mesh_name)

        return


    def diff_xml(self, mesh_xml_old, mesh_xml_new):
        d_old_meshes, l_old_order = self.xml_to_dict(mesh_xml_old, '|')
        d_new_meshes, l_new_order = self.xml_to_dict(mesh_xml_new, '|')

        for mesh_name in d_new_meshes.keys():
            if not mesh_name in d_old_meshes:
                self.l_new.append(mesh_name)
            else:
                if d_old_meshes[mesh_name]['path'] != d_new_meshes[mesh_name]['path']:
                    self.l_moved.append(mesh_name)
                if d_old_meshes[mesh_name]['topology'] != d_new_meshes[mesh_name]['topology']:
                    self.l_topology_changed.append(mesh_name)
                if d_old_meshes[mesh_name]['vertex'] != d_new_meshes[mesh_name]['vertex']:
                    self.l_vtx_num.append(mesh_name)

        for mesh_name in d_old_meshes.keys():
            if not mesh_name in d_new_meshes:
                self.l_missing.append(mesh_name)

        return
