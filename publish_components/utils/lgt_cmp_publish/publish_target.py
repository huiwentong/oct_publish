"""Project-independent, read-only target validation before publish writes."""
from __future__ import annotations

import ntpath
import re

from . import context as context_module
from .modes import validate_publish_mode
from .paths import (
    build_version_dir, build_version_dir_no_num, build_preview_path,
    build_nuke_path, build_version_info_path,
)
from .versions import format_version_key, format_version_name, normalize_version_step


class PublishTargetError(RuntimeError):
    """The selected Task or frozen output no longer matches pipeline data."""


def _require(condition, message):
    if not condition:
        raise PublishTargetError(message + "；请返回表单重新确认任务和版本。")


def _ref(value, entity_type):
    _require(isinstance(value, dict), "缺少{}信息".format(entity_type))
    entity_id = value.get("id")
    _require(
        value.get("type") == entity_type and type(entity_id) is int and entity_id > 0,
        "{}类型或ID无效".format(entity_type),
    )
    return {"type": entity_type, "id": entity_id}


def _name(value, label):
    _require(isinstance(value, str) and bool(value.strip()), label + "为空")
    _require(
        not re.search(r'[<>:"/\\|?*\x00-\x1f]', value)
        and value not in (".", "..") and value == value.strip()
        and not value.endswith("."),
        label + "包含无效路径字符",
    )
    return value


def _path(value):
    _require(isinstance(value, str) and bool(value.strip()), "发布路径为空")
    text = value.replace("\\", "/")
    drive, tail = ntpath.splitdrive(text)
    _require(
        bool(drive) and ntpath.isabs(text) and bool(tail.strip("/"))
        and ".." not in text.split("/") and "\x00" not in text,
        "发布路径必须是完整的绝对路径且不能包含上级目录：{}".format(value),
    )
    return ntpath.normcase(ntpath.normpath(text))


def validate_publish_target(process_data, step, mode, sg=None, resolve_roots=None):
    """Allow any valid Shot Task; reject stale identities or redirected paths.

    GUI and CLI call this through the first process in their shared runlist.
    No directories, permissions, files or ShotGrid records are changed here.
    """
    ctx = process_data.get("publish_context")
    _require(isinstance(ctx, dict), "缺少已确认的发布上下文")
    validate_publish_mode(step, mode)
    _require(ctx.get("publish_mode") == mode, "发布模式与当前流程不一致")
    expected_step = normalize_version_step(step)
    _require(normalize_version_step(ctx.get("step_short_name")) == expected_step,
             "发布环节与当前流程不一致")
    project = _ref(ctx.get("project"), "Project")
    shot = _ref(ctx.get("entity"), "Shot")
    task = _ref(ctx.get("task"), "Task")
    _require(ctx.get("entity_type") == "Shot", "当前工具仅支持镜头任务")
    number = ctx.get("version_num")
    _require(type(number) is int and 1 <= number <= 999, "版本号必须为001至999")

    if sg is None:
        from publish_core.database.core import FastSg

        sg = FastSg().client

    live_task = sg.find_one("Task", [["id", "is", task["id"]]],
                            ["project", "entity", "step", "content"])
    _require(bool(live_task), "ShotGrid中找不到当前任务")
    _require(_ref(live_task.get("project"), "Project") == project,
             "任务所属项目已变化或与表单不一致")
    _require(_ref(live_task.get("entity"), "Shot") == shot,
             "任务所属镜头已变化或与表单不一致")
    live_step_ref = _ref(live_task.get("step"), "Step")
    live_step = sg.find_one("Step", [["id", "is", live_step_ref["id"]]], ["short_name"])
    _require(bool(live_step) and normalize_version_step(live_step.get("short_name")) == expected_step,
             "任务所属环节已变化或不属于当前流程")
    live_project = sg.find_one("Project", [["id", "is", project["id"]]], ["code", "name"])
    live_shot = sg.find_one("Shot", [["id", "is", shot["id"]]], ["code", "project"])
    _require(bool(live_project) and bool(live_shot), "项目或镜头已不存在")
    _require(_ref(live_shot.get("project"), "Project") == project, "镜头与任务不属于同一项目")
    project_name = _name(live_project.get("code") or live_project.get("name"), "项目名称")
    shot_code = _name(live_shot.get("code"), "镜头名称")
    task_content = _name(live_task.get("content"), "任务名称")
    _require(str(ctx.get("project_name") or "").casefold() == project_name.casefold(),
             "项目名称与表单不一致")
    _require(ctx.get("entity_code") == shot_code and ctx.get("task_content") == task_content,
             "镜头或任务名称与表单不一致")

    version_key = format_version_key(shot_code, expected_step, task_content)
    version_name = format_version_name(shot_code, expected_step, task_content, number)
    _require(ctx.get("version_key") == version_key and ctx.get("version_name") == version_name,
             "版本名称与当前任务或版本号不一致")
    # Resolve the same pipeline publish mount used to build the Form, without
    # hardcoding a project, Shot/Task ID or TDTEST directory.
    resolver = resolve_roots or context_module._resolve_roots
    work_root, publish_root = resolver(task["id"], project_name)
    _require(_path(ctx.get("publish_root")) == _path(publish_root),
             "发布根目录与流程配置不一致")
    _require(_path(ctx.get("work_root")) == _path(work_root),
             "工作根目录与流程配置不一致")
    work_key, publish_key = _path(work_root), _path(publish_root)
    _require(
        work_key != publish_key and not publish_key.startswith(work_key + "\\")
        and not work_key.startswith(publish_key + "\\"),
        "工作根与发布根不能重合或互相包含",
    )
    version_dir = build_version_dir(publish_root, version_name)
    expected_paths = {
        "version_dir": version_dir,
        "version_dir_no_num": build_version_dir_no_num(publish_root, version_key),
        "v_dir_preview": build_preview_path(version_dir, version_name),
        "v_dir_nuke": build_nuke_path(version_dir, version_name),
        "v_dir_json": build_version_info_path(version_dir),
    }
    for field, expected in expected_paths.items():
        _require(_path(ctx.get(field)) == _path(expected),
                 "{}不在当前任务对应的版本路径：{}".format(field, ctx.get(field)))
