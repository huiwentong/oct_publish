# -*- coding: utf-8 -*-
import traceback
from importlib import reload
import pymel.core as pm
import maya.utils as utils
import maya.api.OpenMaya as om
from oct.pipeline.task_context import TaskContext
from publish_components.utils import maya_utils
reload(maya_utils)
def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查模型离世界坐标距离 是否
    """
    try:
        task_id = process_data['task_id']
        tc = TaskContext(task_id) or TaskContext.from_env()
        tc.refresh()
        rig_task_status = None
        for t in tc.entity.tasks:
            if t.content == 'rigging':
                rig_task_status = t.sg_status_list
                break

        def get_closest_vertex_to_world_center(group_name):
            """
            遍历所有点，获取离世界中心最近的一个，返回点名称和距离
            """
            group_name = str(group_name)
            sel = om.MSelectionList()
            try:
                sel.add(group_name)
            except RuntimeError:
                om.MGlobal.displayError('Group "{}" not found.'.format(group_name))
                return None, None

            root_path = sel.getDagPath(0)

            # 确保是 transform
            if root_path.apiType() != om.MFn.kTransform:
                om.MGlobal.displayError('"{}" is not a transform.'.format(group_name))
                return None, None

            closest_vertex_name = None
            closest_distance = float("inf")
            world_center = om.MPoint(0.0, 0.0, 0.0)

            it_dag = om.MItDag(om.MItDag.kDepthFirst)
            it_dag.reset(root_path, om.MItDag.kDepthFirst, om.MFn.kMesh)

            while not it_dag.isDone():
                mesh_path = it_dag.getPath()
                mesh_fn = om.MFnMesh(mesh_path)

                # 跳过中间形状
                if mesh_fn.isIntermediateObject:
                    it_dag.next()
                    continue

                points = mesh_fn.getPoints(om.MSpace.kWorld)

                for idx, pt in enumerate(points):
                    dist = pt.distanceTo(world_center)
                    if dist < closest_distance:
                        closest_distance = dist
                        closest_vertex_name = "{}.vtx[{}]".format(
                            mesh_fn.fullPathName(), idx
                        )

                it_dag.next()

            return closest_vertex_name, closest_distance

        if rig_task_status and rig_task_status != 'omt':
            n_root = process_data.get("geo", "|Root_grp")
            n_root = pm.PyNode(n_root)
            vtx, dist = utils.executeInMainThreadWithResult(lambda: get_closest_vertex_to_world_center(n_root))

            if dist > 500:
                msg = "模型距离世界中心距离为{}, 大于500 \n如果该模型为场景元素不进入绑定，请联系制片将该任务的rig状态在SG上改成弃用"
                return msg
    except:
        return traceback.format_exc()


