# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查贴图色彩空间
    """
    try:
        l_unknown_cs = []
        color_list = {'sRGB':'Utility - sRGB - Texture' , 'Raw':'Utility - Raw' }
        ocio_file = utils.executeInMainThreadWithResult(lambda :pm.colorManagementPrefs(q=True, configFilePath=True))
        if not os.path.isfile(ocio_file):
            return "当前场景没有配置 OCIO！！\n可以重新设置下任务环境，再提交！"

        for n_f in pm.ls(type=['file', 'aiImage']):
            n_f_name = n_f.nodeName()
            color_space = n_f.getAttr('colorSpace')
            if color_space in list(color_list.values()):
                continue

            fix_cs = color_list.get(color_space, '')
            if fix_cs:
                n_f.setAttr('colorSpace', fix_cs)
                logger.warning("AUTO FIX: 修改贴图的色彩空间: {} -> {}".format(color_space, fix_cs))
            else:
                l_unknown_cs.append(n_f_name)
        if l_unknown_cs:
            return "以下贴图节点无法自动修复: \n{}".format("\n".join(l_unknown_cs))

    except:
        return traceback.format_exc()


