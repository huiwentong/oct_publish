# -*- coding: utf-8 -*-
import os
import math
import traceback
from pathlib import Path
import maya.cmds as cmds
import maya.utils as utils
from importlib import reload
from oct.pipeline.task_context import TaskContext
from publish_components.utils import maya_utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查角色body模型的拓扑是否与模板一致"""
    # 如果一致，后续会自动输出一个 cfx 用到的头部模型
    try:
        task_id = process_data["task_id"]
        tc = TaskContext(task_id) or TaskContext.from_env()
        sg_asset_type = tc.entity.sg_asset_type
        if sg_asset_type == "CH":

            if cmds.objExists('body_Geo'):
                body_geo_right = True
                vtx_num = cmds.polyEvaluate('body_Geo', v=True)
                if vtx_num == 26344:
                    code_path = Path(maya_utils.__file__).resolve() / "template/check_mod.abc"
                    check_mod_abc = os.path.join(code_path, 'check_mod.abc').replace('\\', '/')
                    logger.info("'body' 模板文件：{}".format(check_mod_abc))
                    cmds.file(check_mod_abc, i=1, type='Alembic', mnc=False)
                    check_mod = 'check_mod'
                    blend = cmds.blendShape('body_Geo', check_mod, origin='local')[0]
                    cmds.setAttr(blend + '.body_Geo', 1)
                    check_ids = [0, 8781, 17562, 26341]
                    for check_id in check_ids:
                        check_arer = cmds.polyEvaluate('check_mod.f[{}]'.format(check_id), fa=True)[0]
                        body_arer = cmds.polyEvaluate('body_Geo.f[{}]'.format(check_id), fa=True)[0]
                        if math.fabs(check_arer - body_arer) > 0.01:
                            cmds.delete('check_mod', blend)
                            body_geo_right = False
                    cmds.delete('check_mod', blend)
                else:
                    body_geo_right = False

                process_data.update({"body_geo_right": body_geo_right})

    except Exception:
        return traceback.format_exc()
