from __future__ import annotations

import os
import re
import subprocess
from typing import Callable, Optional

from publish_components.utils import images

from .errors import FrameRangeError
from .frames import build_frame_range, frame_count_matches_cut, frame_range_for_step
from .preview import (
    PREVIEW_EXR_PNG,
    PREVIEW_IMAGE_SEQUENCE,
    PREVIEW_MOVIE,
    PREVIEW_SINGLE_IMAGE,
    analyze_numbered_sequence,
    classify_preview_paths,
)
from .result import CheckResult
from .versions import format_version_name, get_max_sg_version


DEFAULT_RV_TOOLS = (
    "C:/Program Files/Shotgun/RV-7.7.0/bin/rv.exe",
    "C:/Program Files/Shotgun/RV-7.7.0/bin/rvio_hw.exe",
    "C:/Program Files/Shotgun/RV-7.7.0/bin/rvls.exe",
)


def publish_context(process_data: dict) -> dict:
    """Return the frozen Form context or raise a user-readable error."""
    context = process_data.get("publish_context")
    if not isinstance(context, dict):
        raise ValueError("发布上下文缺失，请返回 Form 页面后重新进入检查")
    return context


def _frame_range(context: dict):
    data = context.get("frame_range")
    if not isinstance(data, dict):
        raise FrameRangeError("ShotGrid Cut/Head/Tail 帧范围缺失")
    return build_frame_range(
        data.get("cut_in"),
        data.get("cut_out"),
        data.get("head_in"),
        data.get("tail_out"),
    )


def check_version_name(process_data: dict) -> CheckResult:
    """Validate the frozen LG Version name against its task context."""
    name = "检查 Version 命名"
    context = publish_context(process_data)
    version_num = context.get("version_num")
    if isinstance(version_num, bool) or not isinstance(version_num, int):
        return CheckResult.fail(name, "版本号必须是三位数字")
    if version_num < 1 or version_num > 999:
        return CheckResult.fail(name, "版本号必须位于 001 到 999 之间")
    expected = format_version_name(
        context.get("entity_code", ""),
        context.get("step_short_name", ""),
        context.get("task_content", ""),
        version_num,
    )
    actual = context.get("version_name")
    if actual != expected:
        return CheckResult.fail(name, "版本名不符合任务上下文：应为 {}，实际为 {}".format(expected, actual))
    return CheckResult.ok(name)


def check_version_increment(process_data: dict) -> CheckResult:
    """Require the selected version to be newer than every existing Version."""
    name = "检查 Version 号递增"
    context = publish_context(process_data)
    current = context.get("version_num")
    if isinstance(current, bool) or not isinstance(current, int):
        return CheckResult.fail(name, "没有取得有效版本号")
    highest = get_max_sg_version(context.get("existing_version_codes") or [])
    if current <= highest:
        return CheckResult.fail(
            name,
            "ShotGrid 已存在 v{:03d}，新版本必须大于该版本".format(highest),
        )
    return CheckResult.ok(name)


def check_cut_range(process_data: dict, shot_data: Optional[dict] = None) -> CheckResult:
    """Validate current ShotGrid Cut/Head/Tail data for LG."""
    name = "检查 ShotGrid 帧范围"
    try:
        context = publish_context(process_data)
        if shot_data is None:
            _frame_range(context)
        else:
            frame_range_for_step(shot_data, context.get("step_short_name", ""))
    except (FrameRangeError, ValueError) as exc:
        return CheckResult.fail(name, str(exc))
    return CheckResult.ok(name)


def check_cmp_cut_range(
    process_data: dict,
    shot_data: Optional[dict] = None,
) -> CheckResult:
    """Validate current ShotGrid Cut In/Out data for CMP, without handles."""
    name = "检查 ShotGrid Cut In/Out"
    try:
        context = publish_context(process_data)
        if shot_data is None:
            data = context.get("frame_range")
            if not isinstance(data, dict):
                raise FrameRangeError("ShotGrid Cut In/Out 缺失")
            build_frame_range(data.get("cut_in"), data.get("cut_out"))
        else:
            build_frame_range(
                shot_data.get("sg_cut_in"),
                shot_data.get("sg_cut_out"),
            )
    except (FrameRangeError, ValueError) as exc:
        return CheckResult.fail(name, str(exc))
    return CheckResult.ok(name)


def check_external_shot(process_data: dict) -> CheckResult:
    """Preserve the legacy check: require a resolved Shot, not a client name."""
    name = "检查外部镜头号"
    context = publish_context(process_data)
    entity = context.get("entity")
    if not isinstance(entity, dict) or not entity.get("id"):
        return CheckResult.fail(name, "没有取得当前 Shot，请返回任务页面重新选择")
    return CheckResult.ok(name)


def check_preview_paths(
    process_data: dict,
    is_file: Callable[[str], bool] = os.path.isfile,
) -> CheckResult:
    """Require at least one existing non-PUR preview file."""
    name = "检查预览文件"
    context = publish_context(process_data)
    selection = classify_preview_paths(context.get("preview_paths") or [])
    if not selection.preview_paths:
        return CheckResult.fail(name, "没有选择有效预览文件；PUR 文件不能代替预览")
    missing = [path for path in selection.preview_paths if not is_file(path)]
    if missing:
        return CheckResult.fail(name, "以下预览文件不存在：\n{}".format("\n".join(missing)))
    return CheckResult.ok(name)


def check_cmp_nuke_source(
    process_data: dict,
    is_file: Callable[[str], bool] = os.path.isfile,
    is_readable: Callable[[str], bool] = lambda path: os.access(path, os.R_OK),
    current_script_path: Optional[Callable[[], Optional[str]]] = None,
) -> CheckResult:
    """Validate the frozen current/manual Nuke source for CMP Publish."""
    name = "检查 CMP Publish 的 Nuke 来源"
    context = publish_context(process_data)
    if context.get("publish_mode") != "Publish":
        return CheckResult.skip(name, "仅 CMP Publish 需要此检查")

    mode = str(context.get("nuke_source_mode") or "").lower()
    if mode not in ("current", "manual"):
        return CheckResult.fail(name, "Nuke 来源模式无效，请返回 Form 重新选择")

    path = str(context.get("script_path") or "").strip().replace("\\", "/")
    if not path:
        return CheckResult.fail(name, "没有取得 Nuke 文件路径")
    if not path.lower().endswith(".nk"):
        return CheckResult.fail(name, "Nuke 来源文件必须是 .nk：{}".format(path))
    if not is_file(path):
        return CheckResult.fail(name, "找不到 Nuke 文件：{}".format(path))
    if not is_readable(path):
        return CheckResult.fail(name, "Nuke 文件不可读：{}".format(path))

    version_key = str(context.get("version_key") or "")
    basename = os.path.basename(path)
    if not version_key or not re.match(
        r"^{}\.v\d{{3}}\.nk$".format(re.escape(version_key)),
        basename,
        re.IGNORECASE,
    ):
        return CheckResult.fail(
            name,
            "Nuke 文件名与当前任务不一致，应匹配 {}.v###.nk".format(
                version_key or "<task>"
            ),
        )

    if mode == "current":
        if current_script_path is None:
            from .nuke_scene import get_nuke_script_path
            current_script_path = get_nuke_script_path
        live_path = str(current_script_path() or "").strip().replace("\\", "/")
        if not live_path:
            return CheckResult.fail(name, "当前 Nuke 工程尚未保存")
        if os.path.normcase(live_path) != os.path.normcase(path):
            return CheckResult.fail(
                name,
                "Form 中冻结的 Nuke 文件已不是当前工程，请返回 Form 重新读取",
            )

    return CheckResult.ok(name, "Nuke 来源模式：{}".format(mode))


def check_cmp_publish_preview(
    process_data: dict,
    shot_data: Optional[dict] = None,
) -> CheckResult:
    """Accept a MOV or require a complete numbered EXR sequence for Publish."""
    name = "检查 CMP Publish 预览/EXR 序列"
    context = publish_context(process_data)
    if context.get("publish_mode") != "Publish":
        return CheckResult.skip(name, "仅 CMP Publish 需要此检查")

    selection = classify_preview_paths(context.get("preview_paths") or [])
    if selection.kind == PREVIEW_MOVIE:
        return CheckResult.ok(name, "Publish 使用 MOV 预览")
    if selection.kind not in (PREVIEW_SINGLE_IMAGE, PREVIEW_IMAGE_SEQUENCE):
        return CheckResult.fail(
            name,
            "CMP Publish 只接受一个 MOV 或一套编号 EXR 序列",
        )
    if any(os.path.splitext(path)[1].lower() != ".exr" for path in selection.preview_paths):
        return CheckResult.fail(name, "CMP Publish 的图片预览必须全部是 EXR")

    try:
        if shot_data is None:
            frame_range = _frame_range(context)
        else:
            frame_range = build_frame_range(
                shot_data.get("sg_cut_in"),
                shot_data.get("sg_cut_out"),
            )
        analysis = analyze_numbered_sequence(
            selection.preview_paths,
            expected_first=frame_range.cut_in,
            expected_last=frame_range.cut_out,
        )
    except Exception as exc:
        return CheckResult.fail(name, "无法解析 EXR 序列：{}".format(exc))

    if analysis.duplicate_frames:
        return CheckResult.fail(
            name,
            "EXR 序列存在重复帧：{}".format(
                ", ".join(str(frame) for frame in analysis.duplicate_frames[:10])
            ),
        )
    if analysis.missing_frames:
        return CheckResult.fail(
            name,
            "EXR 序列缺帧：{}".format(
                ", ".join(str(frame) for frame in analysis.missing_frames[:10])
            ),
        )
    if analysis.unexpected_frames:
        return CheckResult.fail(
            name,
            "EXR 序列包含 Cut 范围外帧：{}".format(
                ", ".join(str(frame) for frame in analysis.unexpected_frames[:10])
            ),
        )
    return CheckResult.ok(name, "EXR 序列：{}".format(analysis.pattern))


def _probe_movie_frame_count(path: str) -> int:
    _, _, frame_count = images.get_info_by_ffprobe(path)
    return frame_count


def check_movie_range(
    process_data: dict,
    probe: Callable[[str], int] = _probe_movie_frame_count,
    shot_data: Optional[dict] = None,
) -> CheckResult:
    """For a single MOV, require its frame count to match ShotGrid Cut."""
    name = "检查 MOV 帧范围"
    context = publish_context(process_data)
    if context.get("skip_movie_range_check") is True:
        return CheckResult.skip(name, "用户已选择跳过 MOV 帧数检查")
    selection = classify_preview_paths(context.get("preview_paths") or [])
    if selection.kind != PREVIEW_MOVIE:
        return CheckResult.ok(name)
    try:
        if shot_data is None:
            frame_range = _frame_range(context)
        else:
            frame_range = build_frame_range(
                shot_data.get("sg_cut_in"),
                shot_data.get("sg_cut_out"),
            )
        frame_count = probe(selection.preview_paths[0])
    except Exception as exc:
        return CheckResult.fail(name, "无法读取 MOV 帧数：{}".format(exc))
    if not frame_count_matches_cut(frame_count, frame_range):
        return CheckResult.fail(
            name,
            "MOV 为 {} 帧，ShotGrid Cut 范围要求 {} 帧".format(
                frame_count,
                frame_range.cut_duration,
            ),
        )
    return CheckResult.ok(name)


def check_preview_frames(
    process_data: dict,
    is_file: Callable[[str], bool] = os.path.isfile,
) -> CheckResult:
    """Validate the legacy LG single-frame EXR+PNG review pair when selected."""
    name = "检查单帧 EXR+PNG"
    context = publish_context(process_data)
    selection = classify_preview_paths(context.get("preview_paths") or [])
    if selection.kind != PREVIEW_EXR_PNG:
        return CheckResult.ok(name)
    missing = [path for path in selection.preview_paths if not is_file(path)]
    if missing:
        return CheckResult.fail(name, "单帧预览文件不存在：\n{}".format("\n".join(missing)))
    return CheckResult.ok(name)


_STATUS_UNSET = object()


def check_status(
    process_data: dict,
    entity_status=_STATUS_UNSET,
    task_status=_STATUS_UNSET,
) -> CheckResult:
    """Apply LG status rules, preferring statuses queried at Check time."""
    name = "检查镜头和任务状态"
    context = publish_context(process_data)
    if entity_status is _STATUS_UNSET:
        entity_status = context.get("entity_status")
    if task_status is _STATUS_UNSET:
        task_status = context.get("task_status")
    normalized_entity_status = str(entity_status or "").lower()
    normalized_task_status = str(task_status or "").lower()
    if normalized_entity_status in ("fin", "omt"):
        return CheckResult.fail(
            name,
            "镜头状态为 {}，不能提交新版本，请联系 PC".format(
                normalized_entity_status
            ),
        )
    if normalized_task_status == "rdone":
        return CheckResult.fail(name, "任务状态为 rdone，不能提交新版本，请联系 PC")
    return CheckResult.ok(name)


def check_cmp_status(
    process_data: dict,
    entity_status=_STATUS_UNSET,
    task_status=_STATUS_UNSET,
) -> CheckResult:
    """Apply CMP status rules, preferring statuses queried at Check time."""
    name = "检查镜头和任务状态"
    context = publish_context(process_data)
    if entity_status is _STATUS_UNSET:
        entity_status = context.get("entity_status")
    if task_status is _STATUS_UNSET:
        task_status = context.get("task_status")
    normalized_entity_status = str(entity_status or "").lower()
    normalized_task_status = str(task_status or "").lower()
    if normalized_entity_status in ("omt", "hld"):
        return CheckResult.fail(
            name,
            "镜头状态为 {}，不能提交新版本，请联系 PC".format(
                normalized_entity_status
            ),
        )
    if normalized_task_status in ("omt", "hld"):
        return CheckResult.fail(
            name,
            "任务状态为 {}，不能提交新版本，请联系 PC".format(
                normalized_task_status
            ),
        )
    return CheckResult.ok(name)


def _probe_rvio(path: str) -> str:
    completed = subprocess.run(
        [path],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    return (completed.stderr or "") + (completed.stdout or "")


def check_rv(
    process_data: Optional[dict] = None,
    tools: tuple[str, str, str] = DEFAULT_RV_TOOLS,
    is_file: Callable[[str], bool] = os.path.isfile,
    probe_rvio: Callable[[str], str] = _probe_rvio,
) -> CheckResult:
    """Require the legacy RV toolset and reject an RVIO licence failure."""
    name = "检查 RV/RVIO"
    # Preserve the legacy gate: only rv.exe is mandatory.  The old tool kept
    # RVIO/RVLS paths for later processes but did not reject their absence.
    if not is_file(tools[0]):
        return CheckResult.fail(name, "未找到 RV 工具：{}".format(tools[0]))
    try:
        output = str(probe_rvio(tools[1]) or "")
    except Exception:
        return CheckResult.ok(name)
    if "license" in output.lower() or "licence" in output.lower():
        return CheckResult.fail(name, "RVIO 许可证不可用，请联系 IT")
    return CheckResult.ok(name)
