# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.cmds as cmds
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import dialogs
from publish_components.utils.maya_utils import mesh_intersection_runner as mir
from importlib import reload
reload(mir)
reload(dialogs)

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查模型之间是否穿插以及自穿插"""
    try:
        task_id = process_data["task_id"]
        tc = TaskContext(task_id) or TaskContext.from_env()
        sg_asset_type = tc.entity.sg_asset_type
        if sg_asset_type == "CH":
            n_high = process_data.get("high", '|Root_grp|Geo_grp|high')
            meshes = []
            seen = set()
            descendants = pm.listRelatives(n_high, ad=True, type="mesh", fullPath=True, noIntermediate=True) or []
            for mesh in descendants:
                if mesh in seen:
                    continue
                # 跳过 intermediate shape。
                try:
                    is_intermediate = pm.getAttr(mesh + ".intermediateObject")
                    if is_intermediate:
                        continue
                except Exception:
                    pass
                seen.add(mesh)
                meshes.append(mesh)

            if meshes:
                runner = mir.MeshIntersectionRunner(face_chunk_size=100,
                                                           intersection_threshold=0.2,
                                                           ray_start_offset= 0.001,
                                                           show_progress=bool(parent_widget),
                                                           progress_title=u"模型穿插检查")

                bad_vertices = runner.run(meshes)
                if bad_vertices:
                    msg = "存在一些穿插的模型，并选中了相关顶点！\n请自行判断是否影响下游并修复。如果这些穿插是允许存在的，请跳过该模块。"
                    if parent_widget:
                        result = utils.executeInMainThreadWithResult(
                            lambda: dialogs.message_dialog("提示", msg, ["继续提交", "停止提交"]))
                        if result == "停止提交":
                            utils.executeInMainThreadWithResult(lambda :cmds.select(bad_vertices, add=True))
                            return msg
        utils.executeInMainThreadWithResult(lambda: cmds.select(clear=True))

    except Exception:
        return traceback.format_exc()
