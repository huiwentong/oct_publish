# -*- coding: utf-8 -*-

import os
import shutil
import traceback
# import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
向版本文件夹拷贝预览图片文件
    """
    try:
        def process():
            preview_files = process_data.get('preview_paths', [])
            pur_files = process_data.get('pur_files', [])
            version_dir = process_data.get('version_dir', '')
            version_name = process_data.get('version_name', '')

            if not (len(preview_files) and preview_files[0].lower().endswith('.mov')):
                v_preview_img_dir = version_dir + '/preview_imgs/'
                if not os.path.isdir(v_preview_img_dir):
                    os.makedirs(v_preview_img_dir)

                for i, f_src in enumerate(preview_files):
                    f_ext = f_src.split('.')[-1]
                    f_dst = v_preview_img_dir + version_name + '.{:04d}.{}'.format(i + 1, f_ext)
                    shutil.copyfile(f_src, f_dst)

                for i, f_src in enumerate(pur_files):
                    f_dst = v_preview_img_dir + version_name + '.{:04d}.{}'.format(i + 1, 'pur')
                    shutil.copyfile(f_src, f_dst)

            return None

        process()
        # result = utils.executeInMainThreadWithResult(process)
        # if result:
        #     return result

    except:
        return traceback.format_exc()
