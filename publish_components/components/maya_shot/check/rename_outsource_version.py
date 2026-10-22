# -*- coding: utf-8 -*-
import os
import re
import shutil
import traceback

import maya.cmds as cmds
from publish_components.utils.gen_func import is_outsourcing


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    外包镜头工程按 SG 下一版本号另存 ma 和 maya_usd 下的 usda，并改写 ma 里 Stage 引用的 usda 路径
    """
    # 只在 cli 且是外包文件时执行。外包商不知道 SG 版本，version_num 由 batch_cli 按 SG 下一版本号填好，
    # 这里把文件名对齐到这个版本，后面的 check_work_file / check_stage_file_path 才能通过。
    # 外包原文件保留，另存新版本名，方便回查。
    try:
        outsource_ma = (submit_data.get('ma_file') or '').replace('\\', '/')
        if not parent_widget and process_data.get('is_outsourcing', is_outsourcing(outsource_ma)):
            version_num = process_data.get('version_num')
            if not version_num:
                return u"没有获取到 SG 下一版本号"
            outsource_dir = os.path.dirname(outsource_ma)
            old_stem = os.path.splitext(os.path.basename(outsource_ma))[0]
            new_stem = re.sub(r'v\d{3}$', version_num, old_stem, flags=re.I)
            if new_stem != old_stem:
                new_ma = '{0}/{1}.ma'.format(outsource_dir, new_stem)
                old_usda = '{0}/maya_usd/{1}.usda'.format(outsource_dir, old_stem)
                new_usda = '{0}/maya_usd/{1}.usda'.format(outsource_dir, new_stem)

                with open(outsource_ma, 'rb') as f:
                    ma_content = f.read()
                if os.path.isfile(old_usda):
                    shutil.copyfile(old_usda, new_usda)
                    # 按字节替换，避免 ma 里的中文被编解码弄坏；外包商本地的绝对路径也一并改成 W 盘路径
                    ma_content = re.sub(rb'"[^"\r\n]*maya_usd[^"\r\n]*\.usda"',
                                        lambda _: '"{0}"'.format(new_usda).encode('utf-8'), ma_content)
                    logger.info(u"外包 usda 另存为: {0}".format(new_usda))
                with open(new_ma, 'wb') as f:
                    f.write(ma_content)
                logger.info(u"外包 ma 另存为: {0}".format(new_ma))

                process_data.setdefault('auto_description', {})['outsourcing root'] = outsource_dir
                submit_data['ma_file'] = new_ma
                process_data['dcc_file'] = new_ma
                cmds.file(new_ma, open=True, force=True)
    except:
        return traceback.format_exc()
