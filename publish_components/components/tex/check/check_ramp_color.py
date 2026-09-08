# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from oct.pipeline.task_context import TaskContext
from publish_components.utils.maya_utils import get_upstream_nodes

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Ramp 节点颜色数量"""
    try:
        def check():
            task_id = process_data['task_id']
            tc = TaskContext(task_id) or TaskContext.from_env()
            is_efx = tc.entity.sg_asset_type == "EFX"
            max_colors = 8 if is_efx else 4
            error_type = "efx" if is_efx else "normal"

            er_data = {"normal": set(), "efx": set()}

            for sg_name in process_data["shaders"]:
                upstream_nodes = []
                get_upstream_nodes.iter_upstream(sg_name, upstream_nodes)

                for node_name in upstream_nodes:
                    node = pm.PyNode(node_name)
                    if (
                        node.nodeType() == "ramp"
                        and node.getAttr("colorEntryList", size=True) > max_colors
                    ):
                        er_data[error_type].add(node_name)

            return er_data

        error_data = utils.executeInMainThreadWithResult(check)
        errors = []

        if error_data["normal"]:
            errors.append("颜色多于 4 种的 ramp 节点：\n{}".format("\n".join(error_data["normal"])))

        if error_data["efx"]:
            errors.append("颜色多于 8 种的 EFX ramp 节点：\n{}".format("\n".join(error_data["efx"])))

        if errors:
            return "\n\n".join(errors)

    except Exception:
        return traceback.format_exc()
