# -*- coding: utf-8 -*-
import math
import traceback
import maya.cmds as cmds
import maya.utils as utils
from oct.pipeline.task_context import TaskContext


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
    检查模型离世界坐标距离（用世界空间包围盒计算）
    如果该模型为场景元素不进入绑定，请联系制片标记绑定任务状态为弃用
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

        def get_bbox_min_distance_to_origin(obj):
            """
            用世界空间包围盒计算模型离原点的最近距离，返回 {"bbox": [...], "distance": float}
            """
            # [xmin, ymin, zmin, xmax, ymax, zmax]
            bbox = cmds.exactWorldBoundingBox(obj)

            xmin, ymin, zmin, xmax, ymax, zmax = bbox

            # 原点到 AABB 在每个轴上的最近距离
            dx = max(xmin, 0, -xmax)
            dy = max(ymin, 0, -ymax)
            dz = max(zmin, 0, -zmax)

            distance = math.sqrt(dx * dx + dy * dy + dz * dz)

            return {
                "bbox": bbox,
                "distance": distance
            }

        # 如果它的绑定任务状态为弃用，代表它是一个场景，那么跳过该检查
        if rig_task_status and rig_task_status != 'omt':
            n_root = process_data.get("geo", "|Root_grp")
            print("检查模型离世界坐标距离: {}".format(n_root))
            if not cmds.objExists(str(n_root)):
                print("{} 不存在，跳过该检查".format(n_root))
            else:
                result = utils.executeInMainThreadWithResult(lambda: get_bbox_min_distance_to_origin(str(n_root)))
                dist = result['distance']
                print('BoundingBox: {}'.format(result['bbox']))
                print('离原点最近距离: {}'.format(dist))

                if dist > 500:
                    msg = "模型距离世界中心距离为{}, 大于500 \n如果该模型为场景元素不进入绑定，请联系制片将该任务的rig状态在SG上改成弃用".format(dist)
                    return msg
    except:
        return traceback.format_exc()
