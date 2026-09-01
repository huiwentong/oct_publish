#!/usr/bin/env python
# -*- coding:utf-8 -*-

import traceback
import os
import pymel.core as pm
import maya.cmds as cmds
import maya.utils as utils
from oct.pipeline import path_acs


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
保存资产及指定模型相关的贴图路径,以及nemo节点的json路径
    """
    try:
        def process():
            d_imgs = {'file': {}, 'aiImage': {}}
            for n in pm.ls(type='file'):
                d_imgs['file'][n.nodeName()] = n.getAttr('fileTextureName')
            for n in pm.ls(type='aiImage'):
                d_imgs['aiImage'][n.nodeName()] = n.getAttr('filename')

            # path_acs.symlink(v_dir_imgs, mod_dir_imgs,remove_exists=True)
            for n in pm.ls(type='file'):
                cs = n.getAttr('colorSpace')
                n.setAttr('fileTextureName', './sourceimages/' + os.path.basename(d_imgs['file'][n.nodeName()]))
                n.setAttr('colorSpace', cs, type='string')
            for n in pm.ls(type='aiImage'):
                cs = n.getAttr('colorSpace')
                n.setAttr('filename', './sourceimages/' + os.path.basename(d_imgs['aiImage'][n.nodeName()]))
                n.setAttr('colorSpace', cs, type='string')

            # nomo
            version_data = process_data['version_dir'] + '/data'
            target_dir = process_data['version_dir_no_num'] + '/data'
            path_acs.symlink(version_data, target_dir, remove_exists=True)

            cmds.setAttr(process_data['nemo_node'] + '.nemo',
                         os.path.join(target_dir, os.path.basename(process_data['nemo_json'])).replace('\\', '/'),
                         type='string')
            cmds.setAttr(process_data['nemo_node'] + '.shading',
                         os.path.join(target_dir, os.path.basename(process_data['mat_json'])).replace('\\', '/'),
                         type='string')

            # export occur some issue
            cmds.file(rename=process_data['v_dir_ma_file'])
            cmds.file(save=1, f=1, type="mayaAscii")

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
