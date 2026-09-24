# -*- coding: utf-8 -*-
import os,traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出xgen base几何体abc和曲线abc"""
    try:
        def process():
            version_dir = process_data.get("version_dir")
            abc_root = version_dir + '/alembic'

            if not os.path.exists(abc_root):
                os.makedirs(abc_root)

            cmd = 'AbcExport -j "-frameRange 1 1 -attrPrefix xgen -stripNamespaces -uvWrite -worldSpace -writeUVSets '
            for path in pm.listRelatives('Root_grp|Hair_cfx|Hair_xgenBaseGeo', c=1):
                cmd += '-root {} '.format(path.fullPath())
            cmd += '-file {}/base.abc";'.format(abc_root)
            pm.mel.eval(cmd)

            for i in pm.listRelatives("Hair_curves_cfx", ad=1, c=1, type="nurbsCurve"):
                if i.intermediateObject.get() == 1:
                    continue
                _p = i.getParent()
                try:
                    desc = _p.attachedXgenDesc.get()
                    if not i.hasAttr("attachedXgenDesc"):
                        i.addAttr("attachedXgenDesc", dataType="string")
                    i.attachedXgenDesc.set(desc)
                except:
                    pass

            if pm.listRelatives('Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx', c=1):
                cmd = 'AbcExport -j "-frameRange 1 1 -attr attachedXgenDesc -stripNamespaces -worldSpace '
                for path in pm.listRelatives('Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx', c=1):
                    cmd += '-root {} '.format(path.fullPath())
                cmd += '-file {}/curves.abc";'.format(abc_root)
                pm.mel.eval(cmd)

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()