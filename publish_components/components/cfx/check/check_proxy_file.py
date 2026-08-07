import hou
from PySide2 import QtCore
import traceback
import os


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查代理模型
    """
    try:
        l_invalid_src = []

        _node:hou.SopNode = hou.node(submit_data['rig_path'])
        proxy_file = _node.parm('proxy_file').eval()
        if proxy_file:
            if not os.path.exists(proxy_file):
                l_invalid_src.append(proxy_file)

        if l_invalid_src:
            return u"文件不存在\n  " + '\n  '.join(l_invalid_src)


    except Exception:
        return traceback.format_exc()

