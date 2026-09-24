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
            version_dir = process_data.get("version_dir")
            if not version_dir:
                raise RuntimeError(u"没有获取到 version_dir")

            if cmds.objExists('xgGroom'):
                cmds.delete('xgGroom')

            palettes = xg.palettes()
            pale = palettes[0]
            dess = xg.descriptions(pale)

            guides_grp = cmds.group(name=pale+'_guides', em=1)
            index = 1
            bind_geos = []

            for desc in dess:
                geo = xg.boundGeometry("{}".format(pale), "{}".format(desc))
                bind_geos.extend(geo)

            guides_abc_folder = os.path.join(version_dir, 'alembic4houdini')
            if not os.path.exists(guides_abc_folder):
                path_acs.make_dirs(guides_abc_folder)

            bind_geos = list(set(bind_geos))
            full_baseabc_file = os.path.join(guides_abc_folder, 'base.abc').replace('\\', '/')
            root_string = ''
            for obj in bind_geos:
                root_string += ' -root {}'.format(obj)
            cmd = 'AbcExport -j "-frameRange 1 1 -attrPrefix xgen -stripNamespaces -uvWrite -worldSpace -writeUVSets {} -file {}";'.format(root_string, full_baseabc_file)
            mel.eval(cmd)

            for desc in dess:
                guides = xg.descriptionGuides(desc)
                if guides:
                    cmds.select(desc,r=1)
                    mel.eval('xgmCreateCurvesFromGuides 1 1')
                    curves_grp = cmds.group(name=desc+'_guides', em=1)
                    cmds.parent(curves_grp, guides_grp)
                    xgCurves_grp = 'xgCurvesFromGuides{}'.format(index)
                    index = index+1

                    curves = cmds.listRelatives(xgCurves_grp, c=1, f=1)
                    for curve in curves:
                        shp = cmds.listRelatives(curve, s=1,f=1)[0]
                        if not cmds.objExists(shp + '.attachedXgenDesc'):
                            cmds.addAttr(shp, ln='attachedXgenDesc', dt='string')
                            cmds.setAttr(shp + '.attachedXgenDesc', desc, type='string')

                    cmds.parent(curves,curves_grp)
                    cmds.rename(curves_grp, desc)

                else:
                    pass

            if cmds.objExists('xgGroom'):
                cmds.delete('xgGroom')

            grp = cmds.rename(guides_grp, pale)
            abc_file = 'guides.abc'
            full_abc_file = os.path.join(guides_abc_folder, abc_file).replace('\\','/')
            cmd = 'AbcExport -j "-frameRange 1 1 -attrPrefix xgen -attr attachedXgenDesc -stripNamespaces -uvWrite -worldSpace -writeUVSets -root {} -file {}";'.format(grp, full_abc_file)
            mel.eval(cmd)
            cmds.delete('|{}'.format(pale))

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()