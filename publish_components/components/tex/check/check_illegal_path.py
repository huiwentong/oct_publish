# -*- coding: utf-8 -*-
import os,re
import traceback
import pymel.core as pm

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查 贴图文件路径 不应该有中文，空格，特殊字符
    """
    try:
        name_pattern = re.compile(r'^[A-Za-z0-9_.-]+$')
        folder_pattern = re.compile(r'^[A-Za-z0-9_.:\\/-]+$')
        errs = ''
        for n_f in pm.ls(type=['file', 'aiImage']):
            try:
                tex_path = n_f.fileTextureName.get()
            except:
                tex_path = n_f.filename.get()
            tex_name = os.path.basename(tex_path)
            check_name = tex_name.upper().replace('.<UDIM>', '').replace('_<UDIM>', '')
            tex_dir = os.path.dirname(tex_path)
            if not bool(name_pattern.fullmatch(check_name)) or not bool(folder_pattern.fullmatch(tex_dir)):
                errs += '{}: {}\n'.format(n_f.name(), tex_path)
        if errs:
            return u"贴图文件名应该由数字字母下划线组成，不应该有中文，空格，特殊字符：\n" + errs
    except:
        return traceback.format_exc()


