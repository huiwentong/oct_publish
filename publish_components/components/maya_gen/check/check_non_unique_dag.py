#!/usr/bin/env python  
# -*- coding:utf-8 -*-
""" 
@author:jiongwan
@team : Octmedia TD Department
@file: check_non_unique_dag.py 
@time: 2022/07/29
@contact: wanjw126@126.com
"""
import traceback


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    import maya.cmds as mc

    non_unique_dag_dict = {}

    dag_node_list = mc.ls(dagObjects=True)
    for node in dag_node_list:
        if '|' in node:
            key = node.split('|')[-1]
            if key not in non_unique_dag_dict:
                non_unique_dag_dict[key] = mc.ls(key, dagObjects=True)

    result = ''
    if len(non_unique_dag_dict) > 0:
        result += u'文件内存在重名节点: \n'
        for key, value in non_unique_dag_dict.items():
            result += '{}: {}\n'.format(key, ', '.join(value))

    return result
