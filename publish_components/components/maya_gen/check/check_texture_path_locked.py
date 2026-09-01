# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查贴图路径属性是否锁定
    """
    try:
        def process():
            l_attrs = []
            for node in pm.ls(typ='file'):
                if node.fileTextureName.isLocked():
                    l_attrs.append(node.fileTextureName)

            for node in pm.ls(typ='aiImage'):
                if node.filename.isLocked():
                    l_attrs.append(node.filename)

            return l_attrs

        locked_attrs = utils.executeInMainThreadWithResult(process)
        if locked_attrs:
            process_data['texture_path_locked_attr'] = locked_attrs
            return u'发现以下贴图路径属性被锁定: {0}'.format(', '.join([attr.name() for attr in locked_attrs]))

    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        def process():
            locked_attr = process_data.get('texture_path_locked_attr', [])
            logger.info(u"AUTO FIX: 修复解锁属性: {0}".format(", ".join(locked_attr)))
            for attr in locked_attr:
                attr.unlock()

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
