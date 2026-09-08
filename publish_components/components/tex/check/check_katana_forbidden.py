# -*- coding: utf-8 -*-

import traceback
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.maya_utils import get_upstream_nodes


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 Katana KtoA 不兼容的材质节点"""
    try:
        UNSUPPORTED_MAYA_NODE_TYPES = {"channel", "uvChooser", "colorConstant", "envBall1", "projection", "place3dTexture",
                                       "marble", "brownian", "cloud", "crater", "fluidTexture3D", "granite", "leather",
                                       "mandelbrot3D", "rock", "snow", "solidFractal", "stucco", "volumeNoise", "wood"}

        def check():
            errors = {"aiStandard": set(), "bifrost": set(), "maya": set(), "colorCorrect": set(), "condition": set()}

            for sg_name in process_data["shaders"]:
                upstream_nodes = []
                get_upstream_nodes.iter_upstream(sg_name, upstream_nodes)

                for node_name in upstream_nodes:
                    node = pm.PyNode(node_name)
                    node_type = node.nodeType()

                    if node_type == "aiStandard":
                        errors["aiStandard"].add(node_name)

                    elif node_type.startswith("bifrost"):
                        errors["bifrost"].add(node_name)

                    elif node_type in UNSUPPORTED_MAYA_NODE_TYPES:
                        errors["maya"].add(node_name)

                    elif node_type == "colorCorrect":
                        errors["colorCorrect"].add(node_name)

                    elif node_type == "condition" and node.operation.get() != 0:
                        errors["condition"].add(node_name)

            return errors

        error_data = utils.executeInMainThreadWithResult(check)
        error_msgs = []

        if error_data.get("aiStandard"):
            error_msgs.append("Arnold 已经放弃使用的 aiStandard 节点：\n{}".format(", ".join(error_data["aiStandard"])))

            if error_data.get("bifrost"):
                error_msgs.append("Bifrost 节点：\n{}".format(", ".join(error_data["bifrost"])))

            if error_data.get("maya"):
                error_msgs.append("无法自动转换的节点：\n{}".format(", ".join(error_data["maya"])))

            if error_data.get("colorCorrect"):
                error_msgs.append("colorCorrect 节点（应该用 aiColorCorrect）：\n{}".format(", ".join(error_data["colorCorrect"])))

            if error_data.get("condition"):
                error_msgs.append(
                    "condition 节点的 operation 属性只能用 equal。"
                    "以下 condition 节点需要其他方式实现效果：\n{}".format(", ".join(error_data["condition"])))

        if error_msgs:
            error_msgs.insert(0, "这些材质中需要替换节点：\n{}".format("\n".join(error_msgs)))
            return "\n".join(error_msgs)

    except Exception:
        return traceback.format_exc()
