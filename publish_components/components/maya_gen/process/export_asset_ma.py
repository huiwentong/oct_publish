# -*- coding:utf-8 -*-

import traceback
import os
import pymel.core as pm
import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
保存资产及指定模型相关的贴图路径
    """
    try:
        def process():
            d_imgs = {'file': {}, 'aiImage': {}}
            for n in pm.ls(type='file'):
                d_imgs['file'][n.nodeName()] = n.getAttr('fileTextureName')
            for n in pm.ls(type='aiImage'):
                d_imgs['aiImage'][n.nodeName()] = n.getAttr('filename')

            n_root = pm.PyNode(process_data.get('root', '|Root_grp'))
            n_parent = n_root.getParent()
            n_root.setParent(None)

            # -set image path, would chage file node color space sometimes
            v_dir_ma_file = process_data['v_dir_ma_file']
            v_dir_imgs = process_data['v_dir_imgs']
            print('v_dir_imgs', v_dir_imgs)

            for n in pm.ls(type='file'):
                cs = n.getAttr('colorSpace')
                n.setAttr('fileTextureName', './sourceimages/' + os.path.basename(d_imgs['file'][n.nodeName()]))
                n.setAttr('colorSpace', cs, type='string')
            for n in pm.ls(type='aiImage'):
                cs = n.getAttr('colorSpace')
                n.setAttr('filename', './sourceimages/' + os.path.basename(d_imgs['aiImage'][n.nodeName()]))
                n.setAttr('colorSpace', cs, type='string')

            pm.select(n_root, r=True)
            if pm.objExists('root_jnt'):
                pm.select('root_jnt', add=1)
            if pm.objExists('Sets'):
                pm.select('Sets', add=True, ne=True)

            # export script node
            for node in pm.ls(type="script"):
                if node.name() in ["sceneConfigurationScriptNode"]:  # default node
                    continue
                if node.getAttr("b") or node.getAttr("a"):  # before or after
                    pm.select(node, add=True, ne=True)
            cmds.file(rename=v_dir_ma_file)
            cmds.file(save=1, f=1, type="mayaAscii")

            pm.select(cl=True)
            n_root.setParent(n_parent)

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
