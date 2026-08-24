# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.mel as mel
import maya.utils as utils
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    清理模型几何体的点相对坐标，清理历史
    """
    try:
        #清理模型几何体的点相对坐标
        def clean_vtx_relative_coordination():
            try:
                for s in pm.ls(type='objectSet'):
                    if s.name() == 'defaultLightSet' or s.name() == 'defaultObjectSet':
                        continue
                    if s.type() == 'objectSet':
                        logger.warning("AUTO FIX: 清除objectSet 节点：{}".format(s.name()))
                        pm.lockNode(s, l=False)
                        pm.delete(s)
            except:
                pass

            n_geo = process_data.get('geo', '|Root_grp|Geo_grp')
            pm.select(n_geo, r=True)
            mel.eval('newCluster " -envelope 1";')
            pm.select(n_geo, r=True)
            pm.refresh()

            l_nodes = pm.listRelatives(n_geo, type='mesh', ad=True)
            for n in l_nodes:
                if n.getAttr('vertexNormal', size=True) != 0:
                    logger.warning("AUTO FIX: 清理模型'{}'的点相对坐标".format(n.name()))
                    pm.polyNormalPerVertex(n, ufn=True)

        #清理历史
        def clean_all_history():
            pm.select(all=True)
            mel.eval('DeleteHistory;')
            pm.select(cl=True)

        utils.executeInMainThreadWithResult(clean_vtx_relative_coordination)
        utils.executeInMainThreadWithResult(clean_all_history)

    except:
        return traceback.format_exc()

