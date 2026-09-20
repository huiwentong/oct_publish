# -*- coding:utf-8 -*-

import traceback
import os
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_core.database.entity import SGEntity


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
按high下各组导出UE用fbx
    """
    try:
        def process():
            task_id = process_data["task_id"]
            version_dir = process_data.get('version_dir', '')
            tc = TaskContext(task_id) or TaskContext.from_env()
            sg_asset_type = tc.entity.sg_asset_type

            task = SGEntity('Task', task_id)
            entity_name = task.entity.code

            if sg_asset_type == 'CH':
                fbx_path = version_dir + '/fbx'
                if not os.path.isdir(fbx_path):
                    os.makedirs(fbx_path)

                # bake joint from 0 to 1 frame, cause to export fbx without ctrl
                cmds.setAttr('root_jnt.v', l=0)
                cmds.setAttr('root_jnt.v', 1)
                cmds.setAttr('high.v', l=0)
                cmds.setAttr('high.v', 1)
                if cmds.objExists('view'):
                    cmds.setAttr('view.v', 0)

                cmds.bakeResults('root_jnt', time=(0, 1), sampleBy=1, simulation=1, oversamplingRate=1,
                                 hierarchy='below', preserveOutsideKeys=1, sparseAnimCurveBake=0,
                                 removeBakedAttributeFromLayer=0,
                                 removeBakedAnimFromLayer=0, bakeOnOverrideLayer=0, minimizeRotation=1, controlPoints=0,
                                 shape=1,
                                 disableImplicitControl=1)

                items = cmds.listRelatives('high', c=1)
                for item in items:
                    if cmds.listRelatives(item, c=1):
                        fbx_name = entity_name + '_' + item + '.fbx'
                        full_fbx = os.path.join(fbx_path, fbx_name).replace('\\', '/')
                        cmds.select(item, 'root_jnt', r=1)

                        cmd = 'FBXExportAnimationOnly -v false;\n'
                        cmd += 'FBXExportApplyConstantKeyReducer -v false;\n'
                        cmd += 'FBXExportBakeComplexAnimation -v true;\n'
                        cmd += 'FBXExportBakeComplexStart -v 0;\n'
                        cmd += 'FBXExportBakeComplexEnd -v 0;\n'
                        cmd += 'FBXExportBakeComplexStep -v 1;\n'
                        cmd += 'FBXExportBakeResampleAnimation -v false;\n'
                        cmd += 'FBXExportCacheFile -v 0;\n'
                        cmd += 'FBXExportCameras -v 0;\n'
                        cmd += 'FBXExportConstraints -v 0;\n'
                        cmd += 'FBXExportSkeletonDefinitions -v 0;\n'
                        cmd += 'FBXExportEmbeddedTextures -v true;\n'
                        cmd += 'FBXExportIncludeChildren -v true;\n'
                        cmd += 'FBXExportInputConnections -v true;\n'
                        cmd += 'FBXExportSkins -v 1;\n'
                        cmd += 'FBXExportShapes -v 1;\n'
                        cmd += 'FBXExportSmoothingGroups -v 1;\n'
                        cmd += 'FBXExportSmoothMesh -v 1;\n'
                        # cmd+= 'FBXExportSplitAnimationIntoTakes -v 0;\n'
                        cmd += 'FBXExportTangents -v 0;\n'
                        cmd += 'FBXExportTriangulate -v 0;\n'
                        # cmd+= 'FBXExportUpAxis -v \"y\";\n'
                        cmd += 'FBXExportUseSceneName -v 0;\n'
                        cmd += 'FBXExport -f "%s" -s;' % full_fbx

                        mel.eval(cmd)
            else:
                fbx_path = version_dir + '/fbx'
                if not os.path.isdir(fbx_path):
                    os.makedirs(fbx_path)

                # bake joint from 0 to 1 frame, cause to export fbx without ctrl
                cmds.setAttr('root_jnt.v', l=0)
                cmds.setAttr('high.v', l=0)
                cmds.setAttr('root_jnt.v', 1)
                cmds.setAttr('high.v', 1)
                if cmds.objExists('view'):
                    cmds.setAttr('view.v', 0)
                cmds.bakeResults('root_jnt', time=(0, 1), sampleBy=1, simulation=1, oversamplingRate=1,
                                 hierarchy='below', preserveOutsideKeys=1, sparseAnimCurveBake=0,
                                 removeBakedAttributeFromLayer=0,
                                 removeBakedAnimFromLayer=0, bakeOnOverrideLayer=0, minimizeRotation=1, controlPoints=0,
                                 shape=1,
                                 disableImplicitControl=1)

                fbx_name = entity_name + '_high.fbx'
                full_fbx = os.path.join(fbx_path, fbx_name).replace('\\', '/')
                cmds.select('high', 'root_jnt', r=1)

                cmd = 'FBXExportAnimationOnly -v false;\n'
                cmd += 'FBXExportApplyConstantKeyReducer -v false;\n'
                cmd += 'FBXExportBakeComplexAnimation -v true;\n'
                cmd += 'FBXExportBakeComplexStart -v 0;\n'
                cmd += 'FBXExportBakeComplexEnd -v 0;\n'
                cmd += 'FBXExportBakeComplexStep -v 1;\n'
                cmd += 'FBXExportBakeResampleAnimation -v false;\n'
                cmd += 'FBXExportCacheFile -v 0;\n'
                cmd += 'FBXExportCameras -v 0;\n'
                cmd += 'FBXExportConstraints -v 0;\n'
                cmd += 'FBXExportSkeletonDefinitions -v 0;\n'
                cmd += 'FBXExportEmbeddedTextures -v true;\n'
                cmd += 'FBXExportIncludeChildren -v true;\n'
                cmd += 'FBXExportInputConnections -v true;\n'
                cmd += 'FBXExportSkins -v 1;\n'
                cmd += 'FBXExportShapes -v 1;\n'
                cmd += 'FBXExportSmoothingGroups -v 1;\n'
                cmd += 'FBXExportSmoothMesh -v 1;\n'
                # cmd+= 'FBXExportSplitAnimationIntoTakes -v 0;\n'
                cmd += 'FBXExportTangents -v 0;\n'
                cmd += 'FBXExportTriangulate -v 0;\n'
                # cmd+= 'FBXExportUpAxis -v \"y\";\n'
                cmd += 'FBXExportUseSceneName -v 0;\n'
                cmd += 'FBXExport -f "%s" -s;' % full_fbx

                mel.eval(cmd)
            return None

        result = utils.executeInMainThreadWithResult(process)
        if result:
            return result
    except:
        return traceback.format_exc()
