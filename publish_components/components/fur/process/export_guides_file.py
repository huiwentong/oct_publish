# -*- coding: utf-8 -*-
import os,traceback
import xgenm as xg
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
from oct.pipeline import path_acs

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出 XGen Guides 和生长面 Alembic 文件。"""
    try:
        def process():
            version_dir=process_data.get("version_dir")
            palette=process_data.get("xgen_palette_name")
            descriptions=process_data.get("xgen_descriptions",[])
            bind_geos=process_data.get("xgen_bound_geometry",[])

            if not version_dir:
                raise RuntimeError(u"没有获取到 version_dir")
            if not palette:
                raise RuntimeError(u"没有获取到 xgen_palette_name")
            if not descriptions:
                raise RuntimeError(u"没有获取到 xgen_descriptions")
            if not bind_geos:
                raise RuntimeError(u"没有获取到 xgen_bound_geometry")

            version_dir=str(version_dir).replace("\\","/").rstrip("/")

            if cmds.objExists("xgGroom"):
                cmds.delete("xgGroom")

            guides_grp=cmds.group(name=palette+"_guides",em=True)
            guides_abc_folder=os.path.join(version_dir,"alembic4houdini").replace("\\","/")
            if not os.path.exists(guides_abc_folder):
                path_acs.make_dirs(guides_abc_folder)

            full_baseabc_file="{}/base.abc".format(guides_abc_folder)
            root_string="".join(" -root {}".format(obj) for obj in bind_geos)
            mel.eval(
                'AbcExport -j "-frameRange 1 1 -attrPrefix xgen -stripNamespaces -uvWrite '
                '-worldSpace -writeUVSets {} -file {}";'.format(root_string,full_baseabc_file)
            )

            index=1
            for description in descriptions:
                guides=xg.descriptionGuides(description)
                if not guides:
                    continue

                mel.eval('select -r "{}";'.format(str(description).replace('"','\\"')))
                mel.eval("xgmCreateCurvesFromGuides 1 1")

                curves_grp=cmds.group(name=description+"_guides",em=True)
                cmds.parent(curves_grp,guides_grp)

                xg_curves_grp="xgCurvesFromGuides{}".format(index)
                index+=1
                curves=cmds.listRelatives(xg_curves_grp,c=True,f=True) or []

                for curve in curves:
                    shapes=cmds.listRelatives(curve,s=True,f=True) or []
                    if not shapes:
                        continue
                    shape=shapes[0]
                    if not cmds.objExists(shape+".attachedXgenDesc"):
                        cmds.addAttr(shape,ln="attachedXgenDesc",dt="string")
                    cmds.setAttr(shape+".attachedXgenDesc",description,type="string")

                if curves:
                    cmds.parent(curves,curves_grp)
                cmds.rename(curves_grp,description)

            if cmds.objExists("xgGroom"):
                cmds.delete("xgGroom")

            grp=cmds.rename(guides_grp,palette)
            full_abc_file="{}/guides.abc".format(guides_abc_folder)
            mel.eval(
                'AbcExport -j "-frameRange 1 1 -attrPrefix xgen -attr attachedXgenDesc '
                '-stripNamespaces -uvWrite -worldSpace -writeUVSets -root {} -file {}";'.format(grp,full_abc_file)
            )

            if cmds.objExists("|{}".format(palette)):
                cmds.delete("|{}".format(palette))

            process_data["xgen_base_abc"]=full_baseabc_file
            process_data["xgen_guides_abc"]=full_abc_file

            if logger:
                logger.info(u"Base Alembic 导出完成：{}".format(full_baseabc_file))
                logger.info(u"Guides Alembic 导出完成：{}".format(full_abc_file))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()