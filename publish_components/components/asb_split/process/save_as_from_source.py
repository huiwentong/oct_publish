# -*- coding: utf-8 -*-
import os
import traceback

import maya.cmds as cmds


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    从source.ma文件另存为文件到指定资产
    """
    # 仅农场端使用：场景是从 source.ma 打开的，这里另存成子资产自己的版本文件。
    try:
        maya_file = process_data['v_dir_ma_file']
        ext = os.path.splitext(maya_file)[-1]
        file_type = 'mayaAscii' if ext == '.ma' else 'mayaBinary'

        cmds.file(rename=maya_file)
        cmds.file(save=True, type=file_type, force=True)

        logger.info(u"已另存为: {0}".format(maya_file))

    except:
        return traceback.format_exc()
