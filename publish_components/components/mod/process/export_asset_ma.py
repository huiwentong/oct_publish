# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """导出资产及相关的贴图"""

    try:
        def get_imgs_info():
            imgs_info = {'file': {}, 'aiImage': {}}
            for n in pm.ls(type='file'):
                imgs_info['file'][n.nodeName()] = n.getAttr('fileTextureName')
            for n in pm.ls(type='aiImage'):
                imgs_info['aiImage'][n.nodeName()] = n.getAttr('filename')
            return imgs_info

        def reset_imgs(imgs_d):
            for n in pm.ls(type='file'):
                cs = n.getAttr('colorSpace')
                n.setAttr('fileTextureName', imgs_d['file'][n.nodeName()])
                n.setAttr('colorSpace', cs, type='string')
            for n in pm.ls(type='aiImage'):
                cs = n.getAttr('colorSpace')
                n.setAttr('filename', imgs_d['aiImage'][n.nodeName()])
                n.setAttr('colorSpace', cs, type='string')

        def process():
            d_imgs = get_imgs_info()
            v_dir_imgs = process_data['v_dir_imgs']
            v_dir_ma_file = process_data['v_dir_ma_file']
            n_root = pm.PyNode(process_data.get('root', '|Root_grp'))
            for n in pm.ls(type='file'):
                cs = n.getAttr('colorSpace')
                n.setAttr('fileTextureName', v_dir_imgs + '/' + os.path.basename(d_imgs['file'][n.nodeName()]))
                n.setAttr('colorSpace', cs, type='string')
            for n in pm.ls(type='aiImage'):
                cs = n.getAttr('colorSpace')
                n.setAttr('filename', v_dir_imgs + '/' + os.path.basename(d_imgs['aiImage'][n.nodeName()]))
                n.setAttr('colorSpace', cs, type='string')

            pm.select(n_root, r=True)
            if pm.objExists('Sets'):
                pm.select('Sets', add=True, ne=True)

            # export script node
            for node in pm.ls(type="script"):
                if node.name() in ["sceneConfigurationScriptNode"]:  # default node
                    continue
                if pm.objExists("{}.a".format(node.name())) or pm.objExists("{}.b".format(node.name())):
                    pm.select(node, add=True, ne=True)

            pm.exportSelected(v_dir_ma_file, force=True, options="v=0;", type="mayaAscii", pr=True, es=True)
            pm.select(cl=True)
            reset_imgs(d_imgs)

        utils.executeInMainThreadWithResult(process)


    except Exception:
        return traceback.format_exc()
