# -*- coding: utf-8 -*-

import os
import shutil
import traceback
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
向版本文件夹拷贝预览图片文件
    """
    try:
        def process():
            l_preview_files = process_data.get('preview_paths', [])
            l_pur_files = process_data.get('l_pur_files', [])
            version_dir = process_data.get('version_dir', '')
            version_name = process_data.get('version_name', '')

            if len(l_preview_files) and l_preview_files[0].lower().endswith('.mov'):
                return ""

            v_preview_img_dir = version_dir + '/preview_imgs/'
            if not os.path.isdir(v_preview_img_dir):
                os.makedirs(v_preview_img_dir)

            l_img_files = []
            for i in range(len(l_preview_files)):
                l_img_files.append(l_preview_files[i])

            for i, f_src in enumerate(l_img_files):
                f_ext = f_src.split('.')[-1]
                f_dst = v_preview_img_dir + version_name + '.{:04d}.{}'.format(i + 1, f_ext)
                shutil.copyfile(f_src, f_dst)

            for i, f_src in enumerate(l_pur_files):
                f_dst = v_preview_img_dir + version_name + '.{:04d}.{}'.format(i + 1, 'pur')
                shutil.copyfile(f_src, f_dst)

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
