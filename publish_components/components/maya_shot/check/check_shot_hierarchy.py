# -*- coding: utf-8 -*-
import traceback

import maya.cmds as cmds
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """
    检查镜头文件顶层层级：cam / lay / World 组都要有
    """
    # 最高层级要有 cam / lay / World 三个组，lay 下要有 lights_grp / efx_grp / cache_grp。
    # 缺少的组会直接补建，补不出来才报错。
    try:
        def check():
            missing = []
            for grp_name in ['|cam', '|lay', '|lay|lights_grp', '|lay|efx_grp', '|lay|cache_grp', '|World']:
                if cmds.objExists(grp_name):
                    continue
                try:
                    parent, name = grp_name.rsplit('|', 1)
                    if parent:
                        cmds.createNode('transform', name=name, parent=parent)
                    else:
                        cmds.createNode('transform', name=name)
                    logger.warning(u"AUTO FIX: 补建缺少的组 {0}".format(grp_name))
                except Exception:
                    missing.append(grp_name)
            return missing

        l_missing_grps = utils.executeInMainThreadWithResult(check)
        if l_missing_grps:
            return u"缺少组：" + ' '.join(l_missing_grps)
    except:
        return traceback.format_exc()
