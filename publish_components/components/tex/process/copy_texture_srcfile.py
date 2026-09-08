# -*- coding: utf-8 -*-
import hashlib
import json
import os
import re
import shutil
import traceback
from oct.pipeline import path_acs


def main(submit_data: dict, process_data: dict, parent_widget=None, logger=None):
    """拷贝 Substance 3D Painter 或 Mari 3D 的贴图源文件"""

    def get_md5(f_path):
        """获取文件 MD5"""
        _md5 = hashlib.md5()

        with open(f_path, "rb") as f:
            while True:
                data = f.read(4 * 1024 * 1024)
                if not data:
                    break
                _md5.update(data)

        return _md5.hexdigest()

    def read_manifest(src_dir):
        manifest_file = os.path.join(src_dir, "src_manifest.json")
        if not os.path.isfile(manifest_file):
            return {}

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            files = data.get("files", {})
            if isinstance(files, dict):
                return files

        except Exception:
            if logger:
                try:
                    logger.warning("READ SRC MANIFEST FAILED | {}\n{}".format(manifest_file, traceback.format_exc()))
                except Exception:
                    pass

        return {}

    def build_history_index(root, v_key, v_name):
        """读取存在 src_manifest.json 的历史版本"""

        version_pattern = re.compile(v_key + r".v\d\d\d")
        result = []

        for old_version in sorted(os.listdir(root)):
            if not version_pattern.match(old_version) or old_version >= v_name:
                continue

            src_dir = os.path.join(root, old_version, "sourcefiles")
            manifest = read_manifest(src_dir)

            if not manifest:
                continue

            result.append((src_dir, manifest))

        return result

    def find_file(history_inx, f_name, _md5):
        """通过 src_manifest.json 查找历史版本中相同的源文件"""

        for src_dir, manifest in history_inx:
            info = manifest.get(f_name)
            if not info:
                continue
            if str(info.get("md5", "")).lower() != str(_md5).lower():
                continue

            src_f = os.path.join(src_dir, f_name)
            if os.path.isfile(src_f):
                return src_f

        return None

    def write_manifest(files):
        manifest = {"schema_version": 1, "files": {}}
        for file_n in sorted(files):
            manifest["files"][file_n] = {
                "md5": files[file_n]
            }

        manifest_file = os.path.join(dst_dir, "src_manifest.json")
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
        # src_tex_files 是源 tex 文件，来自 Substance 3D Painter 或 Mari 3D
        src_tex_files = submit_data["src_tex_files"]
        dst_dir = process_data["v_dir_srcs"]
        publish_root = process_data["publish_root"]
        version_key = process_data["version_key"]
        version_name = process_data["version_name"]

        os.makedirs(dst_dir, exist_ok=True)
        history_index = build_history_index(publish_root, version_key, version_name)

        need_link_src = []
        need_link_dst = []
        manifest_files = {}

        for src_file in src_tex_files:
            if not os.path.isfile(src_file):
                continue

            file_name = os.path.basename(src_file)
            md5 = get_md5(src_file)
            dst_file = os.path.join(dst_dir, file_name)
            old_src_file = find_file(history_index, file_name, md5)

            if old_src_file:
                need_link_src.append(old_src_file)
                need_link_dst.append(dst_file)
            else:
                shutil.copy(src_file, dst_file)
            manifest_files[file_name] = md5

        if need_link_src:
            path_acs.symlink_files(need_link_src, need_link_dst, remove_exists=True, hard_link=True)
            write_manifest(manifest_files)

    except Exception:
        return traceback.format_exc()
