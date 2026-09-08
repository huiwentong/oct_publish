# -*- coding: utf-8 -*-
import traceback
import os
import pymel.core as pm
import maya.utils as utils


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查场景中丢失和非 srf 的贴图"""
    try:
        def check():
            low_textures = []
            low_node = process_data.get("low", "|Root_grp|Geo_grp|low")

            if pm.objExists(low_node):
                for mesh in pm.listRelatives(low_node, ad=True, type="mesh") or []:
                    for sg in pm.listConnections(mesh, type="shadingEngine") or []:
                        for mat in pm.listConnections(sg.surfaceShader, d=False) or []:
                            for file_node in pm.listConnections(mat, type="file", d=False) or []:
                                low_textures.append(file_node.fileTextureName.get())

            errors = {}
            for node in pm.ls(type="file"):
                path = node.fileTextureName.get()

                if path in low_textures:
                    continue

                if "//" in path:
                    path = path.replace("//", "/")
                    node.fileTextureName.set(path)

                check_path = path.replace("<UDIM>", "1001").replace( "<udim>", "1001")
                if node.uvTilingMode.get() == 3:
                    continue

                if not os.path.isfile(check_path):
                    errors[node.name()] = path

            for node in pm.ls(type="aiImage"):
                path = node.filename.get()
                if path in low_textures:
                    continue

                if "//" in path:
                    path = path.replace("//", "/")
                    node.filename.set(path)

                if not os.path.isfile(path) and "<UDIM>" not in path.upper():
                    errors[node.name()] = path

            return errors

        error_data = utils.executeInMainThreadWithResult(check)

        if error_data:
            process_data["texture_missing_error_nodes"] = error_data
            return "当前场景中有丢失和非srf的贴图:\n{}".format(
                "\n".join("{} {}".format(node, path) for node, path in error_data.items())
            )

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """删除有问题的贴图节点"""
    try:
        def repair():
            error_data = process_data.get("texture_missing_error_nodes", {})
            for node in error_data:
                pm.delete(node)
                logger.warning("AUTO FIX: 删除有问题的贴图节点 '{}'".format(node))

        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
