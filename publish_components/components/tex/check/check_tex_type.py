# -*- coding: utf-8 -*-

import os
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查贴图文件类型(tif, tiff, exr, jpg, jpeg, png, tga), tx 指回同名 tif 文件"""
    try:
        def check():
            l_invalid_type = []
            for n_f in pm.ls(type=['file', 'aiImage']):
                try:
                    tex_path = n_f.fileTextureName.get()
                except:
                    tex_path = n_f.filename.get()
                tex_ext = tex_path.lower().split('.')[-1]
                if not tex_ext in ['tiff', 'tif', 'exr', 'jpg', 'jpeg', 'png', 'tga']:
                    if tex_ext == 'tx':
                        if os.path.isfile(tex_path[:-2] + 'tif'):
                            n_f.fileTextureName.set(tex_path[:-2] + 'tif')
                        elif os.path.isfile(tex_path[:-2] + 'tiff'):
                            n_f.fileTextureName.set(tex_path[:-2] + 'tiff')
                        else:
                            l_invalid_type.append(n_f.nodeName() + ' ' + tex_path)
                    elif tex_ext == 'txt':
                        try_to_find_ori_path = '.'.join(tex_path.split('.')[:-2])
                        if os.path.isfile(try_to_find_ori_path):
                            try:
                                n_f.fileTextureName.set(try_to_find_ori_path)
                            except:
                                n_f.filename.set(try_to_find_ori_path)
                    else:
                        l_invalid_type.append(n_f.nodeName() + ' ' + tex_path)

            return l_invalid_type

        invalid_type = utils.executeInMainThreadWithResult(check)

        if invalid_type:
            return "贴图类型不是 tif, tiff, exr, jpg, jpeg, png, tga：\n{}".format("\n".join(invalid_type))

    except Exception:
        return traceback.format_exc()

