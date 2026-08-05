# -*- coding: utf-8 -*-
import os
import traceback

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查提交预览文件的路径和命名
    """
    # 检查提交的预览文件是否存在，扩展名是否有效

    try:
        input_preview_files = process_data.get("preview_paths", [])

        l_preview_files = []
        l_pur_files = []
        if len(input_preview_files) == 0:
            return u"还没有选择文件。"

        for file_path_str in input_preview_files:
            file_path = str(file_path_str)

            if not os.path.isfile(file_path):
                return u"找不到这个文件:\n  " + file_path

            if os.path.basename(file_path).lower().endswith('.pur'):
                l_pur_files.append(file_path)
            else:
                l_preview_files.append(file_path)

        if len(l_preview_files) == 0:
            return u"没有给出图片或者 mov 文件，无法生成版本预览"

        process_data.update({"preview_paths": l_preview_files,
                             "pur_files": l_pur_files})

        logger.info("l_preview_files: {}".format(l_preview_files))
        logger.info("l_pur_files: {}".format(l_pur_files))
    except:
        return traceback.format_exc()


