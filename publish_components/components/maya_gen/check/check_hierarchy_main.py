# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
from oct.pipeline.path_acs import old_get_path

def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查层级 - 通用规范, 需要制作材质渲染的物体放在 |Root_grp|Geo_grp|high 组内
    """

    try:

        if not pm.objExists('|Root_grp'):
            return u"找不到最高层级的组 |Root_grp"

        if not pm.objExists('|Root_grp|Geo_grp'):
            return u"找不到保存面的组 |Root_grp|Geo_grp"

        n_geo = pm.PyNode('|Root_grp|Geo_grp')
        l_children = pm.listRelatives(n_geo, c=True)
        if len(l_children) == 0:
            return u"|Root_grp|Geo_grp 组下为空"

        if len(l_children) > 2:
            return u"|Root_grp|Geo_grp 组下只能有high和low"

        if not pm.objExists('|Root_grp|Geo_grp|high'):
            return u"Geo_grp 组下没有 high 组"

        if not pm.objExists('|Root_grp|Geo_grp|low'):
            return u"Geo_grp 组下没有 low 组"

        if not pm.objExists('|Root_grp|Geo_grp|high|body'):
            return u"high 组下没有body组"

        h_children = pm.listRelatives('high', c=True)
        for child in h_children:
            if pm.listRelatives(child, s=1):
                return u'high下面应该是各个类型组，不能直接放模型'

        trans_list = pm.listRelatives('|Root_grp|Geo_grp|high', ad=1, type='transform')
        error_hierarchy_node_list = []
        gpu_loaded = pm.pluginInfo('gpuCache', q=1, loaded=True)
        for trans in trans_list:
            if pm.listRelatives(trans, c=1, type='transform'):
                if pm.listRelatives(trans, c=1, type='mesh'):
                    error_hierarchy_node_list.append(trans.name())
                if gpu_loaded and pm.listRelatives(trans, c=1, type='gpuCache'):
                    error_hierarchy_node_list.append(trans.name())

        if error_hierarchy_node_list:
            return u"存在既有shape子节点又有transform子节点的层级:\n {} \n".format('; '.join(error_hierarchy_node_list))

        process_data.update({
                'root': pm.PyNode('|Root_grp'),
                'geo': pm.PyNode('|Root_grp|Geo_grp'),
                'high': pm.PyNode('|Root_grp|Geo_grp|high'),
                'low': pm.PyNode('|Root_grp|Geo_grp|low') if pm.objExists('|Root_grp|Geo_grp|low') else None,
            })

    except:
        return traceback.format_exc()


