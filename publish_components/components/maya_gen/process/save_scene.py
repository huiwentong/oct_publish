# -*- coding:utf-8 -*-

import os
import stat
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
            if meshs:
                cmds.displaySmoothness(meshs, du=0, dv=0, pw=4, ps=1)

            # CLI 走 mayapy 没有界面：xgen 描述编辑器和视口面板都不存在，
            # getPanel(vis=1) 会返回 None，下面这些只在有 UI 时做
            if cmds.about(batch=True):
                return

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
            # mayapy 下没有 scriptJob 时返回 None 而不是空列表
            for sj in pm.scriptJob(listJobs=True) or []:
                for virus in l_virus:
                    if virus in sj:
                        id = int(sj.split(':')[0])
                        pm.scriptJob(kill=id, force=True)

            for n in pm.ls(type='script'):
                if 'vaccine_gene' in n.name() or 'breed_gene' in n.name():
                    pm.lockNode(n, l=False)
                    pm.delete(n)

            # 病毒会把 vaccine.py 设成只读，直接 os.remove 会 PermissionError，先去掉只读再删
            scripts_dir = os.path.join(pm.internalVar(userAppDir=True), 'scripts')
            for virus_file in ('vaccine.py', 'vaccine.pyc'):
                virus_path = os.path.join(scripts_dir, virus_file)
                if not os.path.isfile(virus_path):
                    continue
                try:
                    os.chmod(virus_path, stat.S_IWRITE)
                    os.remove(virus_path)
                    logger.warning(u"已删除病毒文件: {0}".format(virus_path))
                except OSError as e:
                    logger.warning(u"删除病毒文件失败: {0} ({1})".format(virus_path, e))

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
                    # 这里如果直接  pm.saveFile(force=True) 有时候会报错说需要 rename
                    pm.renameFile(pm.sceneName())
                    pm.saveFile(force=True)
                else:
                    pm.renameFile(pm.sceneName())
                    pm.saveFile(force=True, uiConfiguration=False)
            except:
                return traceback.format_exc()
            return None

        error_msg = utils.executeInMainThreadWithResult(process)
        if error_msg:
            return error_msg

    except:
        return traceback.format_exc()

