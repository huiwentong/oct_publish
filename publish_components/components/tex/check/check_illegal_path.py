# -*- coding: utf-8 -*-
import os,re
import traceback
import pymel.core as pm

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查 贴图文件名
    """
    try:
        p = re.compile('.*[^\w\.]')
        errs = ''
        for n_f in pm.ls(type=['file', 'aiImage']):
            try:
                tex_path = n_f.fileTextureName.get()
            except:
                tex_path = n_f.filename.get()
            f_name = os.path.basename(tex_path)
            if p.match(f_name.upper().replace('.<UDIM>', '').replace('_<UDIM>', '')):
                errs += '{}: {}\n'.format(n_f.name(), f_name)
        if errs:
            return u"贴图文件名应该由数字字母下划线组成，不应该有中文，空格，特殊字符：\n" + errs
    except:
        return traceback.format_exc()


