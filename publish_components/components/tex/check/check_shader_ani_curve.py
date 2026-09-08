# -*- coding: utf-8 -*-

import traceback
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.maya_utils import get_upstream_nodes

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Shader 动画曲线连接节点是否添加 anim_description 属性"""
    try:
        ANIM_DESCRIPTION_ATTR = "anim_description"
        def check():
            data = {}
            anim_curve_types = pm.nodeType("animCurve", derived=True, isTypeName=True)

            for sg_n in process_data["d_srf_shaders"]:
                upstream_nodes = []
                get_upstream_nodes.iter_upstream(sg_n, upstream_nodes)
                error_nodes = set()

                for node in upstream_nodes:
                    if pm.nodeType(node) not in anim_curve_types:
                        continue

                    for output_node in pm.PyNode(node).outputs():
                        if not output_node.hasAttr(ANIM_DESCRIPTION_ATTR):
                            error_nodes.add(output_node.name())

                if error_nodes:
                    data[sg_n] = sorted(error_nodes)

            return data

        error_data = utils.executeInMainThreadWithResult(check)
        if error_data:
            errors = []
            process_data["shader_anim_curve_error_nodes"] = error_data
            for sg_name, nodes in error_data.items():
                errors.append("{}: {}".format(sg_name,  ", ".join(nodes)))
            return "有些 Shader 上连了动画曲线，且未添加 {} 属性：\n{}".format(ANIM_DESCRIPTION_ATTR, "\n".join(errors))

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """为动画曲线连接节点添加 anim_description 属性"""
    try:
        def repair():
            ANIM_DESCRIPTION_ATTR = "anim_description"
            error_data = process_data.get("shader_anim_curve_error_nodes",{})

            for nodes in error_data.values():
                for node_name in nodes:
                    node = pm.PyNode(node_name)
                    node.addAttr(ANIM_DESCRIPTION_ATTR, dataType="string")
                    logger.warning("AUTO FIX: 为 '{}' 添加 '{}' 属性".format(node_name, ANIM_DESCRIPTION_ATTR,))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
