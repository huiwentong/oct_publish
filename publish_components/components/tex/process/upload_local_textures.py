# -*- coding: utf-8 -*-
import os
import re
import json
import shutil
import traceback
import pymel.core as pm
from oct.pipeline import path_acs
from oct_maya.utils.maya_utils import texture_utils
from publish_components.utils.maya_utils.dialogs import ProgressUI, run_in_maya_main_thread


def main(submit_data, process_data, parent_widget=None, logger=None):
    """
    将资产使用的本地贴图发布到 I 盘
    """
    progress = None

    def prepare_process_data():
        pm.loadPlugin("mtoa", quiet=True)
        pm.arnoldFlushCache(textures=True)
        return pm.colorManagementPrefs(query=True, renderingSpaceName=True)

    def _unique_textures(a_textures):
        result = []
        seen = set()

        for node_name in sorted(a_textures):
            textures = a_textures[node_name]

            for path in sorted(textures):
                if path in seen:
                    continue

                seen.add(path)
                result.append((path, textures[path]))

        return result

    def _tx_paths(tex_p, color_s):
        src_name, suffix = tex_p.rsplit(".", 1)
        return "{}_{}_{}.{}.tx".format(src_name, color_s, render_space, suffix), src_name + ".tx"

    def _read_manifest(s_dir):
        manifest_file = os.path.join(s_dir, "textures_manifest.json")
        if not os.path.isfile(manifest_file):
            return {}

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            textures = data.get("textures", {})
            if isinstance(textures, dict):
                return textures

        except Exception:
            log("READ MANIFEST FAILED | {}\n{}".format(manifest_file, traceback.format_exc()), "warning")

        return {}

    def _build_history_index(p_root, v_key, v_name):
        """
        只读取存在 textures_manifest.json 的历史版本。

        textures_manifest.json 位于：
            sourceimages/textures_manifest.json

        贴图位于：
            sourceimages/4096/
        """

        pattern = re.compile(v_key + r".v\d\d\d")
        result = []

        for version in sorted(os.listdir(p_root)):
            if not pattern.match(version) or version >= v_name:
                continue

            sourceimages_dir = os.path.join(p_root, version, "sourceimages")
            img_dir = os.path.join(sourceimages_dir, "4096")

            try:
                files = set(os.listdir(img_dir))
            except OSError:
                continue

            manifest = _read_manifest(sourceimages_dir)
            if not manifest:
                continue

            result.append((img_dir, files, manifest))

        return result

    def _find_history_texture(history_inx, tex_name, md5, color_space):
        """
        只通过 textures_manifest.json 查找历史贴图。

        MD5 一致：
            原始贴图内容一致。

        color_space / render_space 一致：
            历史 TX 可以安全复用。
        """

        for img_dir, files, manifest in history_inx:
            info = manifest.get(tex_name)

            if not info:
                continue

            if str(info.get("md5", "")).lower() != str(md5).lower():
                continue

            if info.get("color_space") != color_space:
                continue

            if info.get("render_space") != render_space:
                continue

            tx_name = info.get("tx")

            if not tx_name:
                continue

            if tex_name not in files or tx_name not in files:
                continue

            return {
                "img_dir": img_dir,
                "tx_path": os.path.join(img_dir, tx_name)
            }

        return None

    def _collect_textures(u_textures, history_inx):
        result = {}

        for path, info in u_textures:
            progress.step(u"查找历史贴图:\n{}".format(path))
            tex_name = os.path.basename(path)
            md5 = info["md5"]
            color_space = info["colorSpace"]
            history = _find_history_texture(history_inx, tex_name, md5, color_space)
            result[path] = {
                "md5": md5,
                "color_space": color_space,
                "img_dir": history["img_dir"] if history else "",
                "history_tx": history["tx_path"] if history else ""
            }

        return result

    def _hardlink_files(src_ps, dst_ps):
        if not src_ps:
            return
        path_acs.symlink_files(src_ps, dst_ps, remove_exists=True, hard_link=True)

    def _publish_original(texs, dst_d):
        link_src = []
        link_dst = []

        for path in sorted(texs):
            progress.step(u"发布原始贴图:\n{}".format(path))
            info = texs[path]
            tex_name = os.path.basename(path)
            dst_tex = os.path.join(dst_d, tex_name)
            img_dir = info["img_dir"]

            if img_dir:
                link_src.append(os.path.join(img_dir, tex_name))
                link_dst.append(dst_tex)
            else:
                shutil.copyfile(path, dst_tex)

        _hardlink_files(link_src, link_dst)

    def _publish_tx(texs, dst_d):
        link_src = []
        link_dst = []

        for path in sorted(texs):
            progress.step(u"发布 TX:\n{}".format(path))
            info = texs[path]
            tex_name = os.path.basename(path)
            color_space = info["color_space"]
            history_tx = info["history_tx"]
            dst_tex = os.path.join(dst_d, tex_name)
            dst_tx = os.path.join(dst_d, tex_name.rsplit(".", 1)[0] + ".tx")

            # 历史 manifest 已经确认 TX 可以复用
            if history_tx:
                link_src.append(history_tx)
                link_dst.append(dst_tx)
                continue

            # 当前本地贴图附近是否已经存在 TX
            src_tx = next(
                (
                    candidate
                    for candidate in _tx_paths(path, color_space)
                    if os.path.isfile(candidate)
                ),
                None
            )

            if src_tx:
                shutil.copyfile(src_tx, dst_tx)
                continue

            try:
                texture_utils.single_file_make_tx(input_file=dst_tex, colorspace=color_space, output_file=dst_tx)
            except Exception:
                logger.warning("MAKE TX FAILED | {}\n{}".format(path, traceback.format_exc()), "error")

        _hardlink_files(link_src, link_dst)

    def _write_manifest(texs):
        manifest = {"schema_version": 1, "textures": {}}

        for path in sorted(texs):
            tex_name = os.path.basename(path)
            info = texs[path]

            manifest["textures"][tex_name] = {
                "md5": info["md5"],
                "color_space": info["color_space"],
                "render_space": render_space,
                "tx": tex_name.rsplit(".", 1)[0] + ".tx"
            }

        manifest_file = os.path.join(sourceimages_dir, "textures_manifest.json")
        temp_file = manifest_file + ".tmp"

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
            os.replace(temp_file, manifest_file)

        finally:
            if os.path.isfile(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    try:
        asset_textures = process_data["d_asset_tex"]
        publish_root = process_data["publish_root"]
        version_key = process_data["version_key"]
        version_name = process_data["version_name"]
        version_dir = process_data["version_dir"]
        sourceimages_dir = version_dir + '/sourceimages'
        dst_dir = process_data["v_dir_imgs"]
        render_space = run_in_maya_main_thread(prepare_process_data)
        unique_textures = _unique_textures(asset_textures)
        texture_count = len(unique_textures)
        progress = ProgressUI(title=u"发布贴图", maximum=max(1, texture_count * 3 + 1),
                              parent=parent_widget, enabled=bool(parent_widget), logger=logger)
        progress.show(u"准备发布贴图...")
        os.makedirs(dst_dir, exist_ok=True)
        path_acs.unlock_path(dst_dir)
        history_index = _build_history_index(publish_root, version_key, version_name)
        textures = _collect_textures(unique_textures, history_index)
        _publish_original(textures, dst_dir)
        _publish_tx(textures, dst_dir)
        progress.step(u"写入 textures_manifest.json...")
        _write_manifest(textures)
        progress.finish(u"贴图发布完成")

    except Exception:
        error = traceback.format_exc()
        logger.error(error, "error")
        return error

    finally:
        if progress:
            progress.close()
