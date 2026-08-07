# -*- coding:utf-8 -*-
"""
===========================================
项目名称: int
文件: copy_rig_file
作者: huiwentong
创建时间: 2025/10/10
版本: 1.0.0
联系方式: 1120267329@qq.com
描述:
    ******
===========================================
"""

# -*- coding: utf-8 -*-

import os
import shutil
import traceback
import hou
import json

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
向版本文件夹 拷贝/创建 rig和proxy文件
    """
    try:

        def check_sim(node: hou.SopNode):
            is_empty = True
            for _node in node.children():
                if not _node.name().startswith('Python'):
                    is_empty = False
                    break
            return is_empty

        _node:hou.SopNode = hou.node(submit_data['rig_path'])

        cloth_sim = _node.node('oct_build_cloth_sim')
        hair_sim = _node.node('oct_build_hair_sim2')
        proxy_file = _node.parm('proxy_file').eval()

        if proxy_file:
            new_proxy_file = process_data['version_dir'].replace('\\', '/') + '/' + os.path.basename(proxy_file)
            shutil.copyfile(proxy_file, new_proxy_file)
        else:
            new_proxy_file = ''


        rig_json = {
            _node.path(): '/obj/OCT_TMP/cfx_rig_node',
            'proxy_file': new_proxy_file,
            'upstream_version': _node.comment(),
            'cloth_sim': check_sim(cloth_sim),
            'hair_sim': check_sim(hair_sim),
        }

        with open(process_data['version_dir'] + '/rig_data.json', 'w') as f:
            json.dump(rig_json, f, indent=4)

        new_hip_file = process_data['version_dir'] + '/' + os.path.basename(hou.hipFile.path())
        shutil.copyfile(hou.hipFile.path(), new_hip_file)
    except:
        return traceback.format_exc()





