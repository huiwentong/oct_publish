# -*- coding: utf-8 -*-
import traceback
import pymel.core as pm
import maya.utils as utils

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """检查角色眼睛玻璃体相关设置"""
    # 眼睛玻璃体 shader: ThinWalled,Caustics 不启用；shape：Diffuse Reflection属性关闭；眼睛虹膜材质球需要连接高光贴图；
    try:
        def is_cornea_shader_invalid(shader):
            """检查眼睛玻璃体 Shader 参数是否需要修复"""
            CORNEA_SHADER_ATTRS = ("thinWalled", "caustics", "transmitAovs")
            return (
                    all(shader.hasAttr(attr) for attr in CORNEA_SHADER_ATTRS)
                    and any(shader.attr(attr).get() != 0 for attr in CORNEA_SHADER_ATTRS)
            )

        def check():
            data = {"shaders": set(), "shapes": set(), "eyeball_shaders": set(),}
            n_high = process_data.get("high", "|Root_grp|Geo_grp|high")

            for grp in pm.listRelatives(n_high, ad=True, type="transform", fullPath=True,):
                if not grp.nodeName().endswith("_Eye"):
                    continue

                for mesh in pm.listRelatives(grp, ad=True, type="mesh", fullPath=True,):
                    for sg in pm.listConnections(mesh, type="shadingEngine") or []:
                        shaders = pm.listConnections(sg.aiSurfaceShader) or []
                        if not shaders:
                            continue

                        shader = shaders[0]
                        mesh_name = mesh.nodeName()

                        if mesh_name.endswith("_Cornea_geoShape") or "_Cornea" in mesh_name:
                            if is_cornea_shader_invalid(shader):
                                data["shaders"].add(shader.name())

                            if mesh.aiVisibleInDiffuseReflection.get() != 0:
                                data["shapes"].add(mesh.longName())

                        elif mesh_name.endswith("_Eyeball_geoShape") or "_Eyeball" in mesh_name:
                            if not shader.specularColor.connections():
                                data["eyeball_shaders"].add(shader.name())

            return {
                key: sorted(value)
                for key, value in data.items()
            }

        error_data = utils.executeInMainThreadWithResult(check)
        errors = []

        if error_data["shaders"]:
            errors.append("需要调整参数的眼睛玻璃体 shader:\n{}".format("\n".join(error_data["shaders"])))

        if error_data["shapes"]:
            errors.append("需要调整参数的眼睛玻璃体 shape:\n{}".format("\n".join(error_data["shapes"])))

        if error_data["eyeball_shaders"]:
            errors.append("无法自动修复，需要手动连接高光贴图的 shader:\n{}".format("\n".join(error_data["eyeball_shaders"])))

        if errors:
            process_data["eye_shader_error_nodes"] = error_data
            return "\n\n".join(errors)

    except Exception:
        return traceback.format_exc()


def fix(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复眼睛玻璃体 Shader 和 Shape 设置"""
    try:
        def repair():
            CORNEA_SHADER_ATTRS = ("thinWalled", "caustics", "transmitAovs")
            error_data = process_data.get("eye_shader_error_nodes", {})
            for name in error_data.get("shaders", []):
                shader = pm.PyNode(name)

                for attr in CORNEA_SHADER_ATTRS:
                    shader.attr(attr).set(0)
                logger.warning("AUTO FIX: 修复眼睛玻璃体 shader '{}'".format(name))

            for name in error_data.get("shapes", []):
                pm.PyNode(name).aiVisibleInDiffuseReflection.set(0)
                logger.warning("AUTO FIX: 关闭 '{}' 的 Diffuse Reflection".format(name))


        utils.executeInMainThreadWithResult(repair)

    except Exception:
        return traceback.format_exc()
