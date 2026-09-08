# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils
from publish_components.utils.maya_utils import get_upstream_nodes

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查 aiMixShader 输出连接是否合法"""
    try:
        def check():
            VALID_MIX_SHADER_OUTPUT_TYPES = {"aiMixShader", "aiSwitch", "aiLayerShader", "displacementShader", "shadingEngine"}

            er_nodes = set()
            for sg_name in process_data["shaders"]:
                upstream_nodes = []
                get_upstream_nodes.iter_upstream(sg_name, upstream_nodes)

                for node_name in upstream_nodes:
                    node = pm.PyNode(node_name)

                    if node.nodeType() != "aiMixShader":
                        continue

                    for output_node in pm.listConnections(node.outColor, source=False, destination=True,):
                        if output_node.nodeType() not in VALID_MIX_SHADER_OUTPUT_TYPES:
                            er_nodes.add("{} <> {}".format(node.name(), output_node.name()))
            return er_nodes

        error_nodes = utils.executeInMainThreadWithResult(check)
        if error_nodes:
            return ("aiMixShader 节点与非 aiMixShader、aiSwitch、aiLayerShader、"
                    "displacementShader、shadingEngine 类型节点连接：\n  {}").format("\n  ".join(error_nodes))

    except Exception:
        return traceback.format_exc()
