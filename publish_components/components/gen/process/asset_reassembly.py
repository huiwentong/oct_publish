# -*- coding: utf-8 -*-
import traceback, os
from pxr import Sdf
from collections import OrderedDict
from oct.pipeline.task_context import TaskContext
from oct.pipeline.path_acs import lock_path, unlock_path, copy, make_dirs, remove

def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """submit时，重新组装资产的asb usd文件"""

    try:
        task_id = process_data.get("task_id")
        publish_root = process_data["publish_root"]
        publish_type = process_data.get("publish_type", "")
        tc = TaskContext(task_id) or TaskContext.from_env()

        def reassembly_asb(usd_file: str, layer_paths: list[str]) -> None:
            """
            替换 USD/USDA 文件中的所有 subLayers。

            Args:
                usd_file: 要修改的 USD/USDA 文件路径。
                layer_paths: 新的 subLayer 文件路径列表。如：["../tex/a.tex.usda", "../mod/a.mod.usda", "../rig/a.rig.usda"]
            """
            layer = Sdf.Layer.FindOrOpen(usd_file)
            if layer is None:
                raise RuntimeError(f"无法打开 USD 文件: {usd_file}")

            layer.subLayerPaths.clear()

            for path in layer_paths:
                layer.subLayerPaths.append(path)

            if not layer.Save():
                raise RuntimeError(f"保存 USD 文件失败: {usd_file}")

        def reassembly_step(usd_file, variant_data, _step):
            """
            清空所有 variant 的 version，
            然后只保留 variant_data 中指定的版本。

            variant 不存在时直接跳过。
            """
            layer = Sdf.Layer.FindOrOpen(usd_file)
            if not layer:
                raise RuntimeError(f"无法打开 USD 文件: {usd_file}")

            default_prim_name = layer.defaultPrim
            if not default_prim_name:
                raise RuntimeError(f"USD 没有 defaultPrim: {usd_file}")

            prim_path = Sdf.Path("/" + default_prim_name)
            prim_spec = layer.GetPrimAtPath(prim_path)
            step_pass_str = "{}_pass".format(_step)
            step_version_str = "{}_version".format(_step)
            
            if not prim_spec:
                raise RuntimeError(f"找不到 defaultPrim: {prim_path}")

            if step_pass_str not in prim_spec.variantSets:
                raise RuntimeError(f"{prim_path} 中不存在 {step_pass_str} variantSet")

            pass_spec = prim_spec.variantSets[step_pass_str]
            existing_variants = set(pass_spec.variants.keys())
            with Sdf.ChangeBlock():
                for variant_name in existing_variants:
                    variant_spec = pass_spec.variants[variant_name]
                    variant_prim_spec = variant_spec.primSpec
                    if step_version_str in variant_spec.variantSets:
                        del variant_spec.variantSets[step_version_str]

                    variant_prim_spec.variantSetNameList.RemoveItemEdits(step_version_str)
                    if step_version_str in variant_prim_spec.variantSelections:
                        del variant_prim_spec.variantSelections[step_version_str]

                for variant_name, version_data in variant_data.items():
                    # USD 中没有这个 variant，直接跳过, mod 没有变体
                    if variant_name not in existing_variants and _step != 'mod':
                        continue
                    if not version_data:
                        continue

                    variant_spec = pass_spec.variants[variant_name]
                    variant_prim_spec = variant_spec.primSpec
                    version_set_spec = Sdf.VariantSetSpec(variant_spec, step_version_str)
                    variant_prim_spec.variantSetNameList.Prepend(step_version_str)
                    for version, reference_path in version_data.items():
                        version_spec = Sdf.VariantSpec(version_set_spec, version)
                        reference = Sdf.Reference(reference_path, prim_path)
                        version_spec.primSpec.referenceList.Prepend(reference)

                    # 默认选择最后传入的版本
                    selected_version = next(reversed(version_data))
                    variant_prim_spec.variantSelections[step_version_str] = selected_version

            if not layer.Save():
                raise RuntimeError(f"保存 USD 文件失败: {usd_file}")

        def ger_task_variant_data(_step, step_usd_file):
            variant_data = {}
            for _task in tc.entity.tasks:
                if not _task.step.short_name.lower() == _step:
                    continue

                variant_name = "default" if _step == "mod" else _task.content
                # 获取一个任务的最后一版 和 所有submit versions
                last_version = _task.latest_version_by_types(["Submit", "Publish"])
                versions = _task.versions(filters=[['sg_version_type', 'is', 'Submit']],
                                          order=[{'field_name': 'id', 'direction': 'asc'}]) or []
                if last_version not in versions:
                    versions.append(last_version)

                if not versions:
                    continue

                version_data = OrderedDict()
                for version in versions:
                    v_num = version.code.rsplit(".", 1)[1]

                    v_comp_usd = os.path.join(os.path.dirname(version.sg_path_to_geometry), "usd/comp.usda")
                    if not os.path.isfile(v_comp_usd):
                        v_comp_usd = os.path.join(os.path.dirname(version.sg_path_to_geometry), "usd/comp.usd")
                    if not os.path.isfile(v_comp_usd):
                        continue

                    if version.sg_version_type == "Submit":
                        v_comp_usd = os.path.relpath(v_comp_usd, os.path.dirname(step_usd_file))

                    v_comp_usd = v_comp_usd.replace("\\", "/")
                    version_data.update({v_num: v_comp_usd})
                variant_data.update({variant_name: version_data})
            return variant_data

        def find_all_step_usd():
            all_files = []
            asset_all_steps = ["mod", "tex", "fur", "rig", "cfx"]
            publish_asset_root = os.path.dirname(publish_root)
            for step in asset_all_steps:
                step_dir = os.path.join(publish_asset_root, step)
                step_usd_file = os.path.join(step_dir, "{}.{}.usda".format(tc.entity_name, step))
                step_usd_file = step_usd_file.replace("\\", "/")
                # 如果submit 缺少环节usd， 直接找该环节publish对应的文件
                if not os.path.isfile(step_usd_file):
                    step_usd_file = step_usd_file.replace("w:/temp/submit/", "i:/", 1)
                    if os.path.isfile(step_usd_file):
                        all_files.append(step_usd_file)
                else:
                    # 如果该环节submit存在, 还要保证 step usd 里是最新版本的
                    task_variant_data = ger_task_variant_data(step, step_usd_file)
                    reassembly_step(step_usd_file, task_variant_data, step)
                    step_usd_file = os.path.relpath(step_usd_file, os.path.dirname(asb_usda_file))
                    all_files.append(step_usd_file)
            return all_files

        if publish_type.lower() == "submit":
            asb_usda_file = os.path.join(os.path.dirname(publish_root), "asb/{}.usda".format(tc.entity_name))
            all_step_usd_files = find_all_step_usd()
            reassembly_asb(asb_usda_file, all_step_usd_files)

    except Exception:
        return traceback.format_exc()
