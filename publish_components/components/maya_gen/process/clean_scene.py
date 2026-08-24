# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
import maya.mel as mel
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """清理场景，删除非法节点，优化场景大小"""

    try:

        def process():
            off_options = ['deformerOption', 'locatorOption', 'unusedNurbsSrfOption', 'nurbsCrvOption', 'pbOption',
                           'expressionOption', 'poseOption', 'cachedOption', 'transformOption',
                           'partitionOption', 'kRemovingUnusedBrushes', 'ptConOption', 'unusedSkinInfsOption',
                           'setsOption']

            clean_options = ['nurbsSrfOption', 'displayLayerOption', 'renderLayerOption',
                             'animationCurveOption', 'groupIDnOption',
                             'shaderOption', 'shaderOption', 'ptConOption', 'snapshotOption',
                             'unitConversionOption', 'referencedOption',
                             'brushOption', 'unknownNodesOption', 'clipOption']

            for option in off_options:
                pm.optionVar(intValue=(option, False))

            for option in clean_options:
                pm.optionVar(intValue=(option, True))

            os.environ['MAYA_TESTING_CLEANUP'] = '1'
            mel.eval('source cleanUpScene.mel')
            mel.eval('cleanUpScene(1)')
            os.environ['MAYA_TESTING_CLEANUP'] = ''

            for option in clean_options:
                pm.optionVar(intValue=(option, False))

            if pm.objExists('defaultLegacyAssetGlobals'):
                pm.lockNode('defaultLegacyAssetGlobals', lock=False)
                pm.delete('defaultLegacyAssetGlobals')
        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()
