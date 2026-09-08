# -*- coding: utf-8 -*-
import os
import stat
import hashlib
import traceback
from collections import OrderedDict
from publish_components.utils.maya_utils.dialogs import ProgressUI, parallel_map


def main(submit_data, process_data, parent_widget=None, logger=None):
    """
    检查贴图 MD5，避免同名不同内容的贴图互相覆盖
    """
    STAT_WORKERS = 8
    MD5_WORKERS = 4
    MD5_CHUNK_SIZE = 4 * 1024 * 1024
    MD5_RETRY_COUNT = 2

    def _mtime_ns(_st):
        value = getattr(_st, "st_mtime_ns", None)
        if value is not None:
            return value
        return int(_st.st_mtime * 1000000000)

    def _safe_stat(_p):
        try:
            return os.stat(_p)
        except (OSError, IOError):
            return None

    def _is_project_path(_p):
        _p = os.path.normpath(_p).replace("\\", "/").lower()
        return _p == "i:/projects" or _p.startswith("i:/projects/")

    def _name_key(_p):
        return os.path.basename(_p).lower()

    def _cache_matches(_cache, _st):
        if not isinstance(_cache, dict) or not _cache.get("md5") or _cache.get("fsize") != _st.st_size:
            return False
        # 新缓存
        cached_ns = _cache.get("mtime_ns")
        if cached_ns is not None:
            return cached_ns == _mtime_ns(_st)
        # 老缓存兼容
        return _cache.get("mtime") == _st.st_mtime

    def _calculate_md5(_p):
        last_error = None
        for _ in range(MD5_RETRY_COUNT + 1):
            try:
                before = os.stat(_p)
                _md5 = hashlib.md5()
                with open(_p, "rb") as stream:
                    while True:
                        data = stream.read(MD5_CHUNK_SIZE)
                        if not data:
                            break
                        _md5.update(data)
                after = os.stat(_p)
                # 文件读取期间没变化
                if before.st_size == after.st_size and _mtime_ns(before) == _mtime_ns(after):
                    return _md5.hexdigest(), after
                last_error = RuntimeError("Texture changed while reading: {}".format(_p))
            except Exception as exc:
                last_error = exc
        raise RuntimeError("MD5 failed: {}\n{}".format(_p, last_error))

    def _collect_paths(a_textures):
        result = OrderedDict()
        t_refs = 0
        for textures in a_textures.values():
            t_refs += len(textures)
            for _p in textures:
                key = _name_key(_p)
                if key not in result:
                    result[key] = {
                        "name": os.path.basename(_p),
                        "paths": OrderedDict(),
                    }
                # dict 同时完成：
                # 1. 去重
                # 2. 保留第一次出现顺序
                result[key]["paths"].setdefault(_p, None)
        return result, t_refs

    def _collect_all_paths(n_paths):
        result = OrderedDict()
        for group in n_paths.values():
            for _p in group["paths"]:
                result.setdefault(_p, None)
        return result

    def _find_missing_paths(all_paths, file_stats):
        result = []
        for _p in all_paths:
            _st = file_stats.get(_p)
            if _st is None or not stat.S_ISREG(_st.st_mode):
                result.append(_p)
        return result

    def _find_duplicate_conflicts(n_paths, file_stats, path_md5):
        result = []
        for group in n_paths.values():
            paths = []
            for _p in group["paths"]:
                _st = file_stats.get(_p)
                if _st is None or not stat.S_ISREG(_st.st_mode):
                    continue
                if not path_md5.get(_p):
                    continue
                paths.append(_p)

            # 只有一个有效路径
            if len(paths) <= 1:
                continue

            md5_groups = OrderedDict()
            for _p in paths:
                _md5 = path_md5[_p]
                md5_groups.setdefault(_md5, []).append(_p)

            # 同名但内容相同
            if len(md5_groups) <= 1:
                continue

            conflict_lines = []
            for _md5, md5_paths in md5_groups.items():
                for _p in md5_paths:
                    conflict_lines.append(u"{}：\n    MD5: {}".format(_p, _md5))

            result.append(u"{}：\n{}".format(group["name"], u"\n".join(conflict_lines)))
        return result

    def _select_preferred_paths(n_paths, file_stats):
        _preferred = {}
        for name_key, group in n_paths.items():
            valid = []
            for _p in group["paths"]:
                _st = file_stats.get(_p)
                if _st is None or not stat.S_ISREG(_st.st_mode):
                    continue
                valid.append((_p, _st))

            if not valid:
                continue

            # 只有一个有效路径
            if len(valid) == 1:
                _preferred[name_key] = valid[0][0]
                continue

            # 非 project 优先
            local_paths = [item for item in valid if not _is_project_path(item[0])]
            candidates = local_paths or valid

            # 只有一个候选
            if len(candidates) == 1:
                _preferred[name_key] = candidates[0][0]
                continue

            # 多个候选选择最新的
            # max 同值时保留第一个
            _preferred[name_key] = max(candidates, key=lambda item: _mtime_ns(item[1]))[0]
        return _preferred

    def _apply_preferred_paths(a_textures, _preferred):
        for node_name, textures in list(a_textures.items()):
            for _path in list(textures):
                name_key = _name_key(_path)
                preferred_path = _preferred.get(name_key)
                if preferred_path is None:
                    continue
                if _path != preferred_path:
                    del textures[_path]

            if not textures:
                del a_textures[node_name]

    def _build_consumers(a_textures):
        _consumers = {}
        for textures in a_textures.values():
            for _path, _info in textures.items():
                _consumers.setdefault(_path, []).append(_info)
        return _consumers

    try:
        asset_textures = process_data["d_asset_tex"]
        texture_cache = process_data.setdefault("d_tex_pathes", {})
        progress = ProgressUI(title=u"记录贴图文件信息", maximum=1000, parent=parent_widget, enabled=True,
                              logger=logger)
        progress.show(u"正在进入贴图检查...")
        progress.update(20, u"正在收集贴图引用...", True)
        name_paths, total_refs = _collect_paths(asset_textures)
        all_paths = _collect_all_paths(name_paths)
        progress.update(70, u"正在检查贴图文件...", True)
        file_stats = parallel_map(all_paths, _safe_stat, STAT_WORKERS, progress=progress,
                                  progress_start=70, progress_end=300, label=u"检查文件状态")
        missing_textures = _find_missing_paths(all_paths, file_stats)
        progress.update(320, u"正在检查 MD5 缓存...", True)
        path_md5 = {}
        md5_jobs = []
        failed_textures = []
        cached_count = 0

        for _path in all_paths:
            _st = file_stats.get(_path)
            if _st is None or not stat.S_ISREG(_st.st_mode):
                continue

            cache = texture_cache.get(_path)
            if not _cache_matches(cache, _st):
                md5_jobs.append(_path)
                continue

            path_md5[_path] = cache["md5"]
            cached_count += 1

            if cache.get("valid") == "false" or cache.get("valid") is False:
                failed_textures.append(u"{}：\n{}".format(os.path.basename(_path), _path))

        md5_total = len(md5_jobs)
        if md5_total:
            progress.update(350, u"准备计算 {} 个贴图 MD5...".format(md5_total), True)

            def on_md5_finished(_path, result, done_count, total):
                _md5, final_stat = result
                path_md5[_path] = _md5
                texture_cache[_path] = {
                    "fsize": final_stat.st_size,
                    "mtime": final_stat.st_mtime,
                    "mtime_ns": _mtime_ns(final_stat),
                    "md5": _md5,
                    "valid": None,
                }

            parallel_map(md5_jobs, _calculate_md5, MD5_WORKERS, progress=progress,
                         progress_start=350, progress_end=750, label=u"计算 MD5", on_result=on_md5_finished)

        progress.update(770, u"正在检查同名贴图...", True)
        duplicate_conflicts = _find_duplicate_conflicts(name_paths, file_stats, path_md5)
        errors = []

        if missing_textures:
            missing_lines = []
            for _path in missing_textures:
                missing_lines.append(u"{}：\n{}".format(os.path.basename(_path), _path))
            errors.append(u"找不到贴图文件：\n{}".format(u"\n".join(missing_lines)))

        if duplicate_conflicts:
            errors.append(u"发现同名不同内容贴图：\n{}".format(u"\n\n".join(duplicate_conflicts)))

        if failed_textures:
            errors.append(u"已损坏的贴图：\n{}".format(u"\n".join(failed_textures)))

        # 检查失败前不修改 asset_textures
        if errors:
            progress.finish(u"贴图检查失败")
            return u"\n\n".join(errors)

        progress.update(820, u"正在整理同名贴图...", True)
        preferred = _select_preferred_paths(name_paths, file_stats)

        progress.update(880, u"正在整理贴图引用...", True)
        _apply_preferred_paths(asset_textures, preferred)
        consumers = _build_consumers(asset_textures)

        for _path, infos in consumers.items():
            _md5 = path_md5.get(_path)
            if not _md5:
                continue
            for _info in infos:
                _info["md5"] = _md5

        progress.finish(u"贴图检查完成")

    except Exception:
        error = traceback.format_exc()
        logger.error(error)
        return error

    finally:
        if progress:
            progress.close()
