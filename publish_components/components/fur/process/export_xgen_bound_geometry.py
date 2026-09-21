# -*- coding: utf-8 -*-
import os,traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 XGen 生长面和动力学曲线 Alembic 缓存。"""
    try:
        def process():
            version_dir=process_data.get("version_dir")
            bind_geos=process_data.get("xgen_bound_geometry",[])

            if not version_dir:
                raise RuntimeError(u"没有获取到 version_dir")
            if not bind_geos:
                raise RuntimeError(u"没有获取到 xgen_bound_geometry")

            version_dir=str(version_dir).replace("\\","/").rstrip("/")
            abc_root="{}/alembic".format(version_dir)
            if not os.path.exists(abc_root):
                os.makedirs(abc_root)

            root_string="".join(" -root {}".format(path) for path in bind_geos)
            base_file="{}/base.abc".format(abc_root)
            mel.eval(
                'AbcExport -j "-frameRange 1 1 -attrPrefix xgen -stripNamespaces '
                '-uvWrite -worldSpace -writeUVSets{} -file {}";'.format(root_string,base_file)
            )
            process_data["xgen_bound_base_abc"]=base_file

            curves_root="|Root_grp|Hair_cfx|Hair_curves|Hair_curves_cfx"
            curve_shapes=cmds.listRelatives(curves_root,ad=True,type="nurbsCurve",f=True) or []

            for shape in curve_shapes:
                if cmds.getAttr(shape+".intermediateObject"):
                    continue
                parents=cmds.listRelatives(shape,parent=True,f=True) or []
                if not parents:
                    continue
                curve=parents[0]
                if not cmds.objExists(curve+".attachedXgenDesc"):
                    continue
                desc=cmds.getAttr(curve+".attachedXgenDesc")
                if not cmds.objExists(shape+".attachedXgenDesc"):
                    cmds.addAttr(shape,ln="attachedXgenDesc",dt="string")
                cmds.setAttr(shape+".attachedXgenDesc",desc or "",type="string")

            curves=cmds.listRelatives(curves_root,c=True,f=True) or []
            if curves:
                root_string="".join(" -root {}".format(path) for path in curves)
                curves_file="{}/curves.abc".format(abc_root)
                mel.eval(
                    'AbcExport -j "-frameRange 1 1 -attr attachedXgenDesc '
                    '-stripNamespaces -worldSpace{} -file {}";'.format(root_string,curves_file)
                )
                process_data["xgen_curves_abc"]=curves_file

            if logger:
                logger.info(u"XGen Alembic 导出完成：{}".format(abc_root))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()