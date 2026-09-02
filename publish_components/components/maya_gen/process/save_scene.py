# -*- coding:utf-8 -*-

import os
import traceback
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
import pymel.core as pm
import xgenm as xg
import xgenm.xgGlobal as xgg
from publish_core.database.entity import FastSg, SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
保存场景，清理可疑 script 节点
    """
    try:
        def display_setting():
            meshs = cmds.ls(type='mesh')
            cmds.displaySmoothness(meshs, du=0, dv=0, pw=4, ps=1)

            if xg.palettes():
                deseditor = xg.ui.createDescriptionEditor(False)
                deseditor.setGlobals(previewSel=False, previewMode=2, clearSel=True, clearMode=1, playblast=0,
                                     clearCache=True, autoCreateMR=True)
                mel.eval('xgmAddExpressions;')
                palettes = xg.palettes()
                for pale in palettes:
                    dess = xg.descriptions(pale)
                    desc = ['"' + x + '"' for x in dess]
                    dess_str = ','.join(desc)
                    cmd = 'xgmPreview -clean {' + dess_str + '}'
                    mel.eval(cmd)

                    deseditor.preview(True)
                    deseditor._DescriptionEditorUI__refreshPalettes()

            visPanel = cmds.getPanel(vis=1)
            for currentPanel in visPanel:
                panelType = cmds.getPanel(to=currentPanel)
                if panelType == 'modelPanel':
                    cmds.modelEditor(currentPanel, e=1, da='wireframe')

        def process():
            sg = FastSg().client
            l_virus = ['sysytenasdasdfsadfsdaf_dsfsdfaasd', 'PuTianTongQing', 'daxunhuan', 'leukocyte']
            for sj in pm.scriptJob(listJobs=True):
                for virus in l_virus:
                    if virus in sj:
                        id = int(sj.split(':')[0])
                        pm.scriptJob(kill=id, force=True)

            for n in pm.ls(type='script'):
                if 'vaccine_gene' in n.name() or 'breed_gene' in n.name():
                    pm.lockNode(n, l=False)
                    pm.delete(n)

            if os.path.isfile(pm.internalVar(userAppDir=True) + '/scripts/vaccine.py'):
                os.system('del /F/S/Q {}'.format(
                    pm.internalVar(userAppDir=True).replace('/', '\\') + '\\scripts\\vaccine.py'))

            if os.path.isfile(pm.internalVar(userAppDir=True) + '/scripts/vaccine.pyc'):
                os.system('del /F/S/Q {}'.format(
                    pm.internalVar(userAppDir=True).replace('/', '\\') + '\\scripts\\vaccine.pyc'))

            display_setting()
            # fps setting
            if "OCT_PROJECT" in os.environ:
                project = sg.find_one("Project", [["name", "is", os.environ["OCT_PROJECT"]]], ["sg_fps"])
                if not project["sg_fps"]:
                    project["sg_fps"] = 24
                cmds.currentUnit(time="{:d}fps".format(int(project["sg_fps"])))

            try:
                task = SGEntity('Task', process_data['task_id'])
                if task.entity.type in ['Shot', 'Sequence']:
                    pm.saveFile(force=True)
                else:
                    pm.saveFile(force=True, uiConfiguration=False)
            except:
                traceback.print_exc()

        return utils.executeInMainThreadWithResult(process)

    except:
        return traceback.format_exc()

