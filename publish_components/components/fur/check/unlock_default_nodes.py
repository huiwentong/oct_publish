# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data:dict,process_data:dict,parent_widget=None,logger=None):
    """检查 Maya 缺省节点是否被锁定，被锁定则自动解锁。"""
    try:
        def process():
            default_nodes=[
                "time1","sequenceManager1","hardwareRenderingGlobals","renderPartition","renderGlobalsList1",
                "defaultLightList1","defaultShaderList1","postProcessList1","defaultRenderUtilityList1",
                "defaultRenderingList1","lightList1","defaultTextureList1","lambert1","particleCloud1",
                "initialShadingGroup","initialParticleSE","initialMaterialInfo","shaderGlow1","dof1",
                "defaultRenderGlobals","defaultRenderQuality","defaultResolution","defaultLightSet",
                "defaultObjectSet","defaultViewColorManager","defaultColorMgtGlobals","hardwareRenderGlobals",
                "characterPartition","defaultHardwareRenderGlobals","ikSystem","hyperGraphInfo","hyperGraphLayout",
                "globalCacheControl","strokeGlobals","dynController1","lightLinker1","shapeEditorManager",
                "poseInterpolatorManager","layerManager","defaultLayer","renderLayerManager","defaultRenderLayer"
            ]

            locked_nodes=[]
            for node_name in default_nodes:
                if not pm.objExists(node_name):
                    continue

                node=pm.PyNode(node_name)
                is_locked=pm.lockNode(node,q=True,lock=True)[0]
                is_unpublished_locked=pm.lockNode(node,q=True,lockUnpublished=True)[0]

                if is_locked or is_unpublished_locked:
                    locked_nodes.append(node_name)

            if locked_nodes:
                if logger:
                    logger.warning(u"发现被锁定的 Maya 缺省节点：{}".format(" ".join(locked_nodes)))

                cant_unlock=[]
                for node_name in locked_nodes:
                    try:
                        if logger:
                            logger.warning(u"AUTO FIX: 解锁缺省节点 {}".format(node_name))

                        node=pm.PyNode(node_name)
                        pm.lockNode(node,lock=False,lockUnpublished=False)
                    except Exception:
                        cant_unlock.append(node_name)

                if cant_unlock:
                    raise RuntimeError(u"无法解锁以下 Maya 缺省节点：{}".format(" ".join(cant_unlock)))

            if logger:
                logger.info(u"Maya 缺省节点锁定检查完成")

        utils.executeInMainThreadWithResult(process)
    except Exception:
        return traceback.format_exc()