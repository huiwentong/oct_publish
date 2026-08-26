# -*- coding: utf-8 -*-
import traceback, os
import pymel.core as pm
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    基本项检查。
    """
    # 1.检查maya 单位为cm 2.清理未知插件 3.清理未知节点 4.解锁maya基本节点
    try:
        if not os.path.exists('C:/Program Files/Autodesk/Maya2024/bin/maya.exe'):
            return "本地没有安装maya 2024!"

        # 检查maya 单位为cm
        current_unit = utils.executeInMainThreadWithResult(lambda: pm.currentUnit(q=True, linear=True))
        if not current_unit == "cm":
            return u"当前单位是%s，请在 Maya 的 Preference 中设为厘米 (cm)" % current_unit

        # 清理未知插件
        l_cant_remove = []
        unknown_plugins = utils.executeInMainThreadWithResult(lambda: pm.unknownPlugin(q=True, list=True)) or []
        for p in unknown_plugins:
            try:
                pm.unknownPlugin(p, r=True)
                logger.warning("开始清理位置插件：{}".format(p))
            except:
                l_cant_remove.append(p)
                pass
        if l_cant_remove:
            return u"无法清除的插件：" + ', '.join(l_cant_remove)

        # 清理未知节点
        if pm.ls('ngSkinToolsData_*'):
            logger.warning("清除 ‘ngskin’ 产生的节点")
            pm.delete('ngSkinToolsData_*')

        unknown_nodes = pm.ls(type='unknown')
        if unknown_nodes:
            for node in unknown_nodes:
                node.setLocked(False)
                logger.warning("开始清理未知节点{}".format(node))
            pm.delete(unknown_nodes)

        # 解锁
        l_defualt_ndoes = [
            'time1', 'sequenceManager1', 'hardwareRenderingGlobals', 'renderPartition', 'renderGlobalsList1',
            'defaultLightList1', 'defaultShaderList1', 'postProcessList1', 'defaultRenderUtilityList1',
            'defaultRenderingList1', 'lightList1', 'defaultTextureList1', 'lambert1', 'particleCloud1',
            'initialShadingGroup', 'initialParticleSE', 'initialMaterialInfo', 'shaderGlow1', 'dof1',
            'defaultRenderGlobals', 'defaultRenderQuality', 'defaultResolution', 'defaultLightSet',
            'defaultObjectSet', 'defaultViewColorManager', 'defaultColorMgtGlobals', 'hardwareRenderGlobals',
            'characterPartition', 'defaultHardwareRenderGlobals', 'ikSystem', 'hyperGraphInfo', 'hyperGraphLayout',
            'globalCacheControl', 'strokeGlobals', 'dynController1', 'lightLinker1', 'shapeEditorManager',
            'poseInterpolatorManager', 'layerManager', 'defaultLayer', 'renderLayerManager', 'defaultRenderLayer'
        ]
        for n_name in l_defualt_ndoes:
            if pm.objExists(n_name):
                n = pm.PyNode(n_name)
                if pm.lockNode(n, q=True, lock=True)[0] or pm.lockNode(n, q=True, lockUnpublished=True)[0]:
                    logger.warning("AUTO FIX: 解锁节点 ‘{}’ ".format(n_name))
                    pm.lockNode(n, lock=False, lockUnpublished=False)
    except:
        return traceback.format_exc()


