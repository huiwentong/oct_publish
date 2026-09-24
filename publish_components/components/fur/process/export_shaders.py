# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 XGen 材质 ma 文件和材质分配信息。"""
    try:
        def process():
            version_dir = process_data.get("version_dir")
            if not version_dir:
                raise RuntimeError(u"没有获取到 version_dir")

            list_sgs=[]
            for sg in pm.ls(type='shadingEngine'):
                if sg in ["initialParticleSE", "initialShadingGroup"]:
                    continue

                assigned_objects = pm.listConnections(sg.name(), s=1, d=0, c=0, p=0, sh=1, type = 'xgmDescription')
                if not assigned_objects:
                    continue

                if not sg.hasAttr('assignedXgmDescriptions'):
                    sg.addAttr('assignedXgmDescriptions', dt='string')
                sg.attr('assignedXgmDescriptions').set(';'.join([obj.name() for obj in assigned_objects]))
                list_sgs.append(sg)

            if not list_sgs:
                raise RuntimeError(u"XGen没有赋给材质")

            pm.select(clear=1)
            pm.select(list_sgs, ne=True, r=True)
            pm.exportSelected(version_dir + '/srf_shaders.ma', force=True)

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()