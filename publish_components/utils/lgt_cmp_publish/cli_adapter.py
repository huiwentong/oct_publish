from __future__ import annotations

import hashlib
import inspect
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Optional

from .cli_request import CHECK_ONLY, EXECUTE, CliPublishRequest
from .errors import PublishError


class CliAdapterError(PublishError):
    """Raised while adapting a validated request to the framework CLI."""


def initialize_cli_interface(interface: Any) -> None:
    """Preserve PublishCli data around the framework's destructive runlist load."""
    original_process_data = dict(interface.process_data or {})
    if not original_process_data.get("task_id"):
        raise CliAdapterError("CLI 初始化缺少 task_id。")

    interface.get_all_check_process()
    runlist_data = dict(interface.process_data or {})
    filetypes = runlist_data.get("filetypes")
    if filetypes is None:
        raise CliAdapterError("CLI 无法从 runlist 读取 filetypes。")

    original_process_data["filetypes"] = filetypes
    interface.process_data = original_process_data
    interface.init_process_data()
    interface.fill_submit_form()
    interface.check_submit_form()
    interface.process_data["is_cli"] = True


def resolve_notify_users(
    user_ids: tuple[int, ...],
    sg: Any = None,
) -> list[dict]:
    if not user_ids:
        return []
    if sg is None:
        from publish_core.database.core import FastSg

        sg = FastSg().client
    rows = sg.find(
        "HumanUser",
        [["id", "in", list(user_ids)]],
        ["id", "name", "login", "sg_dingtalk_id"],
    )
    by_id = {int(row["id"]): dict(row) for row in rows or [] if row.get("id")}
    missing = [str(user_id) for user_id in user_ids if user_id not in by_id]
    if missing:
        raise CliAdapterError(
            "找不到通知人员 ShotGrid ID：{}。".format("、".join(missing))
        )
    result = []
    for user_id in user_ids:
        row = by_id[user_id]
        row.setdefault("type", "HumanUser")
        result.append(row)
    return result


def create_publish_cli(
    request: CliPublishRequest,
    user: Any = None,
    notify_users: Optional[list[dict]] = None,
    publish_cli_cls: Any = None,
    publish_type_map: Optional[dict[str, Any]] = None,
) -> Any:
    """Create and fully initialize the framework PublishCli without a GUI."""
    if publish_cli_cls is None or publish_type_map is None:
        from publish_core.cli import PublishCli, PublishType, get_user

        if publish_cli_cls is None:
            publish_cli_cls = PublishCli
        if publish_type_map is None:
            publish_type_map = {
                "Dailies": PublishType.DAILY,
                "Submit": PublishType.SUBMIT,
                "Publish": PublishType.PUBLISH,
            }
        if user is None:
            user = get_user()
    if user is None:
        raise CliAdapterError("无法确定当前发布用户。")
    if request.publish_type not in publish_type_map:
        raise CliAdapterError(
            "框架无法识别发布模式：{}。".format(request.publish_type)
        )
    if notify_users is None:
        notify_users = resolve_notify_users(request.notify_user_ids)

    return publish_cli_cls(
        user=user,
        task_id=request.task_id,
        gui=False,
        publish_type=publish_type_map[request.publish_type],
        comment=request.comment,
        publish_tag_id=request.publish_tag_id,
        version_num=request.version_num,
        dcc_file=request.dcc_file,
        dcc="Nuke",
        preview_paths=list(request.preview_paths),
        notify=list(notify_users),
        input_form=request.input_form(),
    )


def prepared_cli_result(cli: Any, request: CliPublishRequest) -> dict:
    interface = getattr(cli, "interface", None)
    if interface is None or not interface.process_data:
        raise CliAdapterError("CLI Interface 尚未完成初始化。")
    context = interface.process_data.get("publish_context")
    if not isinstance(context, dict):
        raise CliAdapterError("CLI 未生成冻结的 publish_context。")
    return {
        "ok": True,
        "phase": "prepare",
        "operation": request.operation,
        "task_id": request.task_id,
        "publish_type": request.publish_type,
        "version_name": context.get("version_name"),
        "version_dir": context.get("version_dir"),
        "dcc_file": request.dcc_file,
        "preview_count": len(request.preview_paths),
        "check_count": len(interface.check_files),
        "process_count": len(interface.process_files),
        "nuke_source_mode": context.get("nuke_source_mode"),
        "skip_movie_range_check": context.get("skip_movie_range_check", False),
    }


def _file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _open_nuke_scene(scene_path: str) -> None:
    import nuke

    nuke.scriptOpen(scene_path)
    current = str(nuke.root().name() or "").replace("\\", "/")
    if current.lower() != scene_path.replace("\\", "/").lower():
        raise CliAdapterError(
            "Nuke Terminal 打开的工程与请求不一致：{}。".format(current)
        )


def run_cli_checks(
    cli: Any,
    request: CliPublishRequest,
    component_cls: Any = None,
    scene_opener: Optional[Callable[[str], None]] = None,
    clock: Callable[[], float] = time.perf_counter,
    fingerprint: Callable[[str], str] = _file_sha256,
) -> dict:
    """Run only registered checks, in the same stop-on-failure order as GUI."""
    interface = getattr(cli, "interface", None)
    if interface is None or not interface.process_data:
        raise CliAdapterError("CLI Interface 尚未完成初始化。")
    if request.operation not in (CHECK_ONLY, EXECUTE):
        raise CliAdapterError("检查执行器收到无法识别的 operation。")
    if component_cls is None:
        from publish_components.core import Component

        component_cls = Component
    if scene_opener is None:
        scene_opener = _open_nuke_scene

    check_files = list(interface.check_files)
    filetypes = interface.process_data.get("filetypes") or []
    check_types = list(filetypes[0]) if filetypes else []
    if len(check_types) != len(check_files):
        raise CliAdapterError("runlist 的 check file/type 数量不一致。")

    source_hash_before = fingerprint(request.dcc_file)
    started = clock()
    scene_opener(request.dcc_file)
    rows = []
    stopped_at = None

    for index, check_path in enumerate(check_files):
        component = component_cls(
            interface,
            str(check_path),
            True,
            interface.log,
            check_types[index],
        )
        row_started = clock()
        try:
            component.run()
            error = str(component.status or "")
        except Exception:
            error = traceback.format_exc()
        duration = max(0.0, clock() - row_started)
        description = inspect.getdoc(component.gui_main) or ""
        row = {
            "name": component.name,
            "type": component.type,
            "description": description,
            "status": "failed" if error else "success",
            "error": error,
            "duration_seconds": round(duration, 6),
        }
        rows.append(row)
        if error:
            stopped_at = component.name
            break

    source_hash_after = fingerprint(request.dcc_file)
    source_unchanged = source_hash_before == source_hash_after
    component_checks_executed = len(rows)
    if not source_unchanged:
        if stopped_at is None:
            stopped_at = "source_integrity"
        rows.append(
            {
                "name": "source_integrity",
                "type": "CLI",
                "description": "确认 check-only 未修改源 Nuke 文件。",
                "status": "failed",
                "error": "check-only 运行期间源 Nuke 文件内容发生变化。",
                "duration_seconds": 0.0,
            }
        )

    return {
        "ok": stopped_at is None and source_unchanged,
        "phase": "check",
        "operation": request.operation,
        "task_id": request.task_id,
        "publish_type": request.publish_type,
        "version_name": interface.process_data.get("version_name"),
        "dcc_file": request.dcc_file,
        "checks_registered": len(check_files),
        "checks_executed": component_checks_executed,
        "checks": rows,
        "stopped_at": stopped_at,
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "source_unchanged": source_unchanged,
        "processes_registered": len(interface.process_files),
        "processes_executed": 0,
        "duration_seconds": round(max(0.0, clock() - started), 6),
    }


def run_cli_execute(
    cli: Any,
    request: CliPublishRequest,
    component_cls: Any = None,
    scene_opener: Optional[Callable[[str], None]] = None,
    clock: Callable[[], float] = time.perf_counter,
    fingerprint: Callable[[str], str] = _file_sha256,
) -> dict:
    """Run all checks first, then processes in order with stop-on-failure."""
    if request.operation != EXECUTE or request.execute_confirm != "PUBLISH":
        raise CliAdapterError("execute 执行器缺少双重发布确认。")
    interface = getattr(cli, "interface", None)
    if interface is None or not interface.process_data:
        raise CliAdapterError("CLI Interface 尚未完成初始化。")

    started = clock()
    check_result = run_cli_checks(
        cli,
        request,
        component_cls=component_cls,
        scene_opener=scene_opener,
        clock=clock,
        fingerprint=fingerprint,
    )
    if not check_result.get("ok"):
        result = dict(check_result)
        result["operation"] = EXECUTE
        result["processes"] = []
        result["outputs"] = {}
        result["side_effects_started"] = False
        result["partial_side_effects_possible"] = False
        result["rollback_performed"] = False
        result["duration_seconds"] = round(max(0.0, clock() - started), 6)
        return result

    if component_cls is None:
        from publish_components.core import Component

        component_cls = Component

    process_files = list(interface.process_files)
    filetypes = interface.process_data.get("filetypes") or []
    process_types = list(filetypes[1]) if len(filetypes) > 1 else []
    if len(process_types) != len(process_files):
        raise CliAdapterError("runlist 的 process file/type 数量不一致。")

    rows = []
    stopped_at = None
    for index, process_path in enumerate(process_files):
        component = component_cls(
            interface,
            str(process_path),
            True,
            interface.log,
            process_types[index],
        )
        row_started = clock()
        try:
            component.run()
            error = str(component.status or "")
        except Exception:
            error = traceback.format_exc()
        duration = max(0.0, clock() - row_started)
        description = inspect.getdoc(component.gui_main) or ""
        row = {
            "name": component.name,
            "type": component.type,
            "description": description,
            "status": "failed" if error else "success",
            "error": error,
            "duration_seconds": round(duration, 6),
        }
        rows.append(row)
        if error:
            stopped_at = component.name
            break

    process_data = interface.process_data
    context = process_data.get("publish_context") or {}
    created_version = process_data.get("created_version") or {}
    daily_playlist = process_data.get("daily_playlist") or {}
    outputs = {
        "version_dir": context.get("version_dir"),
        "published_nk": process_data.get("published_nk_path"),
        "published_preview": process_data.get("published_preview_path"),
        "published_version_info": process_data.get("published_version_info"),
        "shotgrid_version_id": (
            created_version.get("id")
            if isinstance(created_version, dict)
            else None
        ),
        "daily_playlist_id": (
            daily_playlist.get("id")
            if isinstance(daily_playlist, dict)
            else None
        ),
        "version_up_workfile": process_data.get("version_up_workfile"),
        "version_up_candidate": process_data.get("version_up_candidate"),
        "workfile_version_up_skipped": bool(
            process_data.get("workfile_version_up_skipped", False)
        ),
        "workfile_version_up_reason": process_data.get(
            "workfile_version_up_reason"
        ),
    }
    result = {
        "ok": stopped_at is None,
        "phase": "publish",
        "operation": EXECUTE,
        "task_id": request.task_id,
        "publish_type": request.publish_type,
        "version_name": interface.process_data.get("version_name"),
        "dcc_file": request.dcc_file,
        "checks_registered": check_result["checks_registered"],
        "checks_executed": check_result["checks_executed"],
        "checks": check_result["checks"],
        "source_sha256_before_checks": check_result["source_sha256_before"],
        "source_sha256_after_checks": check_result["source_sha256_after"],
        "source_unchanged_during_checks": check_result["source_unchanged"],
        "processes_registered": len(process_files),
        "processes_executed": len(rows),
        "processes": rows,
        "outputs": outputs,
        "stopped_at": stopped_at,
        "side_effects_started": bool(rows),
        "partial_side_effects_possible": bool(stopped_at and rows),
        "rollback_performed": False,
        "duration_seconds": round(max(0.0, clock() - started), 6),
    }
    if stopped_at:
        result["recovery_message"] = (
            "发布过程已开始且未自动回滚，请根据已完成过程和日志人工核对现场。"
        )
    return result
