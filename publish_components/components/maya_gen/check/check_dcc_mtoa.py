# -*- coding: utf-8 -*-
import os
import traceback

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查 mota 是否安装并可以使用
    """
    try:
        maya_version = os.environ['MAYA_VERSION']
        if int(maya_version) <= 2020:
            mtoa_maketx = "C:/solidangle/mtoadeploy/{}/bin/maketx.exe".format(maya_version)
        else:
            mtoa_maketx = "C:/Program Files/Autodesk/Arnold/maya{}/bin/maketx.exe".format(maya_version)

        if not os.path.isfile(mtoa_maketx):
            return u"在统一的安装路径下没有找到 mtoa 的转 tx 工具: {}".format(mtoa_maketx)
    except:
        return traceback.format_exc()


