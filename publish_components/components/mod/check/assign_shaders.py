# -*- coding: utf-8 -*-

import traceback

import pymel.core as pm
import maya.utils as utils
import maya.api.OpenMaya as om


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """修复 high 下无材质或使用 initialShadingGroup 的 Mesh / Face"""

    try:

        def get_mesh_shader_info(mesh):
            mesh_path = mesh.longName()
            selection = om.MSelectionList()
            selection.add(mesh_path)

            dag_path = selection.getDagPath(0)
            if dag_path.node().hasFn(om.MFn.kTransform):
                dag_path.extendToShape()

            fn_mesh = om.MFnMesh(dag_path)
            instance_number = dag_path.instanceNumber()
            shader_objects, shader_indices = fn_mesh.getConnectedShaders(instance_number)
            shader_names = []

            for obj in shader_objects:
                fn_dep = om.MFnDependencyNode(obj)
                shader_names.append(fn_dep.name())

            return shader_names, shader_indices

        def check_and_fix():
            n_high = process_data.get("root","|Root_grp|Geo_grp|high")
            fix_sg = None
            for mesh in pm.listRelatives(n_high, ad=True, type="mesh", ni=True, fullPath=True) :
                if "proxyShape" in mesh.nodeName():
                    continue
                shader_names, shader_indices = get_mesh_shader_info(mesh)
                bad_faces = []

                try:
                    initial_sg_index = shader_names.index("initialShadingGroup")
                except ValueError:
                    initial_sg_index = None

                for face_id, shader_index in enumerate(shader_indices):
                    # 没有材质
                    if shader_index == -1:
                        bad_faces.append(face_id)
                        continue

                    # initialShadingGroup
                    if initial_sg_index is not None and shader_index == initial_sg_index:
                        bad_faces.append(face_id)

                if not bad_faces:
                    continue
                face_count = len(shader_indices)

                # 第一次发现问题才创建修复材质
                if fix_sg is None:
                    shader_name = "default_fix_MAT"
                    sg_name = "default_fix_MATSG"

                    if pm.objExists(shader_name):
                        shader = pm.PyNode(shader_name)
                        if shader.nodeType() != "lambert":
                            raise RuntimeError("'{}' 已存在，但不是 lambert！".format(shader_name))
                    else:
                        shader = pm.shadingNode("lambert", asShader=True, name=shader_name)
                        shader.color.set((0.5, 0.5, 0.5))

                    if pm.objExists(sg_name):
                        fix_sg = pm.PyNode(sg_name)
                        if fix_sg.nodeType() != "shadingEngine":
                            raise RuntimeError("'{}' 已存在，但不是 shadingEngine！".format(sg_name))
                    else:
                        fix_sg = pm.sets(empty=True, renderable=True, noSurfaceShader=True, name=sg_name)

                    # 不管 SG 是否原本存在，都确保连接正确
                    pm.connectAttr(shader.outColor, fix_sg.surfaceShader, force=True)

                # 整 Mesh / 部分 Face
                if len(bad_faces) == face_count:
                    target = mesh

                else:
                    target = [mesh.f[index] for index in bad_faces]
                # 修复
                pm.sets(fix_sg, e=True, forceElement=target)
                logger.warning("AUTO FIX：修复 '{}' {} 个无材质或 initialShadingGroup Face！".format(mesh, len(bad_faces)))

        utils.executeInMainThreadWithResult(check_and_fix)

    except Exception:
        return traceback.format_exc()
