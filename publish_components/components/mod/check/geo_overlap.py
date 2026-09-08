# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查疑似完全重叠的几何体"""
    #检查是否有完全重叠的模型（一般是误操作复制）。如果有，需要模型师确认是否为多余物体
    try:
        def check():
            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")
            meshes = pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True)
            transforms = set(mesh.getParent() for mesh in meshes)
            bbox_dict = {}

            for trans in transforms:
                bbox = pm.exactWorldBoundingBox(trans)
                key = tuple(round(v, 8) for v in bbox)
                bbox_dict.setdefault(key, []).append(trans)

            overlapping = [
                nodes for nodes in bbox_dict.values()
                if len(nodes) > 1
            ]
            return overlapping

        overlap_nodes = utils.executeInMainThreadWithResult(check)
        if overlap_nodes:
            msg = ""
            for group in overlap_nodes:
                msg += "疑似完全重叠的模型: {} \n".format(" 和 ".join(str(node) for node in group))
            return msg

    except Exception:
        return traceback.format_exc()
