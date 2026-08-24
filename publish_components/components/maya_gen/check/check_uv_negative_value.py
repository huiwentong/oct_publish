# -*- coding: utf-8 -*-
import math
import traceback
import pymel.core as pm
import maya.api.OpenMaya as om
from oct.pipeline.task_context import TaskContext


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 mesh 的 UV 是否在负象限"""

    try:
        task_id = process_data["task_id"]
        tc = TaskContext(task_id) or TaskContext.from_env()
        sg_asset_type = tc.entity.sg_asset_type

        if sg_asset_type == "CH":
            bad_meshes = {}
            epsilon = 1e-6

            high_group = process_data.get('high', '|Root_grp|Geo_grp|high')
            for mesh in pm.listRelatives(high_group, ad=True, type='mesh', ni=True):
                sel = om.MSelectionList()
                sel.add(mesh.name())

                dag_path = sel.getDagPath(0)
                mesh_fn = om.MFnMesh(dag_path)
                u_array, v_array = mesh_fn.getUVs()

                if not u_array:
                    continue

                bad_uvs = []
                bad_tiles = set()

                for i, (u, v) in enumerate(zip(u_array, v_array)):
                    # 处理接近 0 的浮点误差
                    if abs(u) < epsilon:
                        u = 0.0
                    if abs(v) < epsilon:
                        v = 0.0

                    if u < -epsilon or v < -epsilon:
                        bad_uvs.append(
                            "{}.map[{}]".format(mesh.name(), i)
                        )

                        bad_tiles.add((
                            int(math.floor(u)),
                            int(math.floor(v))
                        ))

                if bad_uvs:
                    bad_meshes[mesh.name()] = {
                        "bad_uvs": bad_uvs,
                        "bad_tiles": bad_tiles
                    }

            if bad_meshes:
                return  "以下 mesh 的 UV 坐标落在负象限，请调整至正向象限：\n{}".format('\n'.join(bad_meshes.keys()))

    except Exception:
        return traceback.format_exc()
