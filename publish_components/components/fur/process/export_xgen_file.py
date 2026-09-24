# -*- coding: utf-8 -*-
import os,traceback
import pymel.core as pm
import maya.utils as utils
import xgenm as xg
from oct.pipeline.task_context import TaskContext

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """导出毛发xgen文件"""
    try:
        def process():
            task_id = process_data["task_id"]
            tc = TaskContext(task_id) or TaskContext.from_env()
            version_dir = process_data["version_dir"]
            origin_paths = process_data["origin_paths"]
            xgen_palette_name = process_data["xgen_palette_name"]
            assetName = tc.entity_name
            xgen_file_path = version_dir + '/{}__{}.xgen'.format(assetName, xgen_palette_name)
            result = xg.exportPalette(str(xgen_palette_name), str(xgen_file_path))
            if not result:
                raise "导出xgen文件失败"

            xgen_palette_node = pm.PyNode(xgen_palette_name)
            origin_paths['xgFileName'] = xgen_palette_node.xgFileName.get()
            xgen_palette_node.xgFileName.set(xgen_file_path)

            pales = xg.palettes()
            for pale in pales:
                pm.setAttr(pale + '.v', 1)
                descs = xg.descriptions(pale)
                for desc in descs:
                    pm.setAttr(desc + '.v', 1)

            hairSystems = pm.ls(type='hairSystem')
            for hs in hairSystems:
                pm.setAttr(hs + '.simulationMethod', 1)
                pm.setAttr(hs + '.active', 0)
            pm.saveFile(f=1)

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()