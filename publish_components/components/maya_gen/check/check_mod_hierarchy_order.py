#!/usr/bin/env python  
# -*- coding:utf-8 -*-
""" 
@author:jiongwan
@team : Octmedia TD Department
@file: check_hierarchy_order.py 
@time: 2023/03/10
@contact: wanjw126@126.com
"""
import traceback
import os
from typing import Any

import maya.cmds as mc
import pymel.core as pm
import xml.etree.ElementTree as ET
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    对比模型版本层级顺序。
    """
    try:

        def get_last_version(mod_v, mod_path):
            v_root = os.path.dirname(os.path.dirname(mod_path))
            v_dir_name = os.path.basename(os.path.dirname(mod_path))
            mesh_xml = None
            tokens = v_dir_name.split('.')
            if len(tokens) == 4 and tokens[-1][0] == 'v' and tokens[-1][1:].isdigit():
                v_key = '.'.join(tokens[:3])
                for dir_name in sorted(os.listdir(v_root)):
                    if dir_name.startswith(v_key + '.v') and dir_name[-3:].isdigit() and os.path.isfile(
                            '{}/{}/mesh.xml'.format(v_root, dir_name)):
                        mesh_xml = '{}/{}/mesh.xml'.format(v_root, dir_name)
                        mod_v = dir_name[-3:]
                return mod_v, mesh_xml
            else:
                if os.path.isfile(os.path.dirname(mod_path) + '/mesh.xml'):
                    return mod_v, os.path.dirname(mod_path) + '/mesh.xml'
                else:
                    return mod_v, mesh_xml

        def parse_xml_hierarchy(xml):
            out_dict = {}
            if not xml:
                return out_dict
            tree = ET.parse(xml)
            root = tree.getroot()
            sub_root_node = {}
            for node in root.iter('transform'):
                # if node.iter('transform'):
                sub_root_node[node.get('name')] = []
                sub_node_list = list(node)
                for sub_node in sub_node_list:
                    if sub_node.tag == 'transform':
                        # if sub_node != node:
                        sub_root_node[node.get('name')].append(sub_node.get('name'))
            for key, value in sub_root_node.items():
                if len(value) and 'high' in key:
                    out_dict[key.split('|')[-1]] = list([v.split('|')[-1] for v in value])
            return out_dict

        def compare_order(target_dict: dict) -> dict[Any, Any]:
            error_grp_dict = {}
            for grp, children_list in target_dict.items():
                if mc.objExists(grp):
                    chilrens = mc.listRelatives(grp, c=1, type='transform')
                    if chilrens != children_list:
                        error_grp_dict[grp] = [chilrens, children_list]
                else:
                    error_grp_dict[grp] = [None, children_list]
            return error_grp_dict

        def process():
            n_root = process_data.get('root', '|Root_grp')
            n_root = pm.PyNode(n_root)
            l_attrs = mc.listAttr(n_root.name())
            mesh_xml = None
            if 'modelVersion' in l_attrs and 'modelPath' in l_attrs:
                mod_version = mc.getAttr(n_root + '.modelVersion')
                mod_path = mc.getAttr(n_root + '.modelPath')
                if mod_path and os.path.isdir(os.path.dirname(mod_path)):
                    mod_version, mesh_xml = get_last_version(mod_version, mod_path)
                    print("mod_version:", mod_version)
                    print("mesh_xml:", mesh_xml)

            result_dict = compare_order(parse_xml_hierarchy(mesh_xml))
            if result_dict:
                for key, value in result_dict.items():
                    target_order_list = value[-1]
                    reversed_order_list = reversed(target_order_list)
                    for grp in reversed_order_list:
                        mc.reorder(grp, front=True)
                logger.info(u"AUTO FIX: 修复层级顺序 {0}".format(result_dict))

        utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
