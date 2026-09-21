#!/usr/bin/env python  
# -*- coding:utf-8 -*-

import glob
import os
import traceback
import json
import maya.cmds as mc
import maya.utils as utils
import pymel.core as pm


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查提交nemo文件是否存在
    """
    try:
        def process():
            nemo_node = mc.ls(type='Nemo')
            if not nemo_node:
                return u'文件内不存在Nemo节点，请检查文件!'

            process_data['nemo_node'] = nemo_node[0]

            work_file = str(pm.sceneName())
            if work_file:
                process_data['nemo_json'] = mc.getAttr(process_data['nemo_node'] + ".nemo").replace('\\', '/')
                process_data['mat_json'] = mc.getAttr(process_data['nemo_node'] + '.shading').replace('\\', '/')
                file_dir = os.path.dirname(work_file)

                if not os.path.isfile(process_data['nemo_json']):
                    process_data['nemo_json'] = os.path.join(file_dir, process_data['nemo_json'])

                if not os.path.isfile(process_data['mat_json']):
                    process_data['mat_json'] = os.path.join(file_dir, process_data['mat_json'])

                if not os.path.isfile(process_data['nemo_json']):
                    return u"ma文件中指定的_CONFIG.json不存在，请重新指定"

                if not os.path.isfile(process_data['mat_json']):
                    return u"ma文件中指定的_MAT.json不存在，请重新指定"

                json_dir = os.path.dirname(process_data['nemo_json'])
                with open(process_data['nemo_json']) as f:
                    info = json.load(f)

                    dll_name = info.get('bin')
                    if dll_name:
                        if not dll_name.endswith('.dll'):
                            dll_name += '.dll'

                    process_data['dll'] = os.path.join(json_dir, dll_name).replace('\\', '/')
                    process_data['resource'] = os.path.join(json_dir, info.get('resource')).replace('\\', '/')

                    if not os.path.isfile(process_data['dll']):
                        return u"CONFIG文件中指定的 dll 文件不存在，请重新指定"

                    if not os.path.isfile(process_data['resource']):
                        return u"CONFIG文件中指定的 resource 文件不存在，请重新指定"

                    # Find export.zip
                    export_zip_files = glob.glob("%s/*__EXPORT.zip" % json_dir)
                    if export_zip_files:
                        process_data['export'] = export_zip_files[0].replace('\\', '/')
                    else:
                        process_data['export'] = None

            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result

    except:
        return traceback.format_exc()
