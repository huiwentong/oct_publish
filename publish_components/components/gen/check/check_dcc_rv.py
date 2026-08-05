# -*- coding: utf-8 -*-
import traceback
import os
import subprocess

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    这是一个用来检查dcc是否有rv的检查项
    """

    try:
        print("@"*100)
        print(process_data)
        dcc_rv = "C:/Program Files/Shotgun/RV-7.7.0/bin/rv.exe"
        dcc_rvio = "C:/Program Files/Shotgun/RV-7.7.0/bin/rvio_hw.exe"
        dcc_rvls = "C:/Program Files/Shotgun/RV-7.7.0/bin/rvls.exe"
        process_data.update({"dcc_rv": dcc_rv, "dcc_rvio": dcc_rvio, "dcc_rvls": dcc_rvls})
        if not os.path.isfile(dcc_rv):
            return u"在统一的安装路径下没有找到 RV 的执行文件: {}".format(dcc_rv)
        try:
            p = subprocess.Popen('"' + dcc_rvio + '"', shell=True, stderr=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            out, err = p.communicate()

            if 'license' in str(err):
                return u"因为许可证的原因，RVIO 无法启动，请联系IT ！"
        except:
            pass

    except:
        return traceback.format_exc()


