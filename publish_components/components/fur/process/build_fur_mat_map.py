# -*- coding: utf-8 -*-

import traceback
import maya.cmds as cmds


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """生成 Fur XGen Description 与材质之间的 USD 映射。"""
    try:
        description_nodes = process_data.get("xgen_description_nodes", [])
        description_transforms = process_data.get("xgen_description_transforms", [])
        if not description_nodes or not description_transforms:
            return u"没有获取到 XGen Description 信息"

        mat_map = {}

        for shape, transform in zip(description_nodes, description_transforms):
            dag_name = transform.replace("\\", "/")
            if "Hair_cfx|" not in dag_name:
                continue

            materials = set()
            for sg in cmds.listConnections(shape, type="shadingEngine") or []:
                materials.update(cmds.listConnections(
                    sg + ".surfaceShader", source=True, destination=False
                ) or [])

            if not materials:
                return u"XGen Description {} 没有找到材质".format(dag_name)

            usd_path = "/hair_cfx/" + dag_name.split("Hair_cfx|", 1)[1].replace("|", "/")
            for material in materials:
                mat_map.setdefault(material, [])
                if usd_path not in mat_map[material]:
                    mat_map[material].append(usd_path)

        if not mat_map:
            return u"Hair_cfx 下没有生成有效的材质映射"

        process_data["mat_map"] = mat_map

        if logger:
            logger.info(u"Fur material map: {}".format(mat_map))
        return ""

    except Exception:
        return traceback.format_exc()