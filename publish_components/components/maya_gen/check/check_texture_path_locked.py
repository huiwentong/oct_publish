# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

locked_attr = []


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
检查贴图路径属性是否锁定
    """
    try:
        def process():
            global locked_attr
            locked_attr = []
            for node in pm.ls(typ='file'):
                if node.fileTextureName.isLocked():
                    locked_attr.append(node.fileTextureName)

            for node in pm.ls(typ='aiImage'):
                if node.filename.isLocked():
                    locked_attr.append(node.filename)

            if locked_attr:
                return u'发现以下贴图路径属性被锁定: {0}'.format(', '.join([attr.name() for attr in locked_attr]))
            else:
                return ""

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    try:
        logger.info(u"AUTO FIX: 修复解锁属性: {0}".format(", ".join(locked_attr)))

        def process():
            for attr in locked_attr:
                attr.unlock()

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()
