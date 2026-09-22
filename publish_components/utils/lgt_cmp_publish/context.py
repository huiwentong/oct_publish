from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .constants import (
    DAILY_MODE,
    SUBMIT_MODE,
    PUBLISH_MODE,
    NUKE_DCC,
)
from .versions import (
    format_version_key,
    format_version_name,
)
from .paths import (
    build_version_dir,
    build_version_dir_no_num,
    build_preview_path,
    build_nuke_path,
    build_version_info_path,
)
from .frames import FrameRange, frame_range_for_step
from .nuke_scene import get_nuke_script_path, is_script_modified


def _resolve_roots(
    task_id: int,
    project_name: str,
) -> tuple[str, str]:
    """
    Resolve the Nuke work root and review-version output root.

    MK2 Nuke workfiles live under the Task's ``work/nuke`` root. Published
    versions live directly under the Task's ``publish`` mount.

    Returns ``(work_root, publish_root)``. The mount contract is W: for work,
    I: for published versions, and R: for render/output media.
    """
    from oct.pipeline.path_acs import old_get_path

    show_name = project_name.upper()
    work_root = old_get_path(
        mount_point='work', show_name=show_name,
        entity_type='Task', id=task_id,
        key='nuke',
    )
    publish_root = old_get_path(
        mount_point='publish', show_name=show_name,
        entity_type='Task', id=task_id,
    )
    return work_root, publish_root


@dataclass
class PublishContext:
    """
    Aggregated publish context for LGT/CMP operations.

    Built once at form submission time and passed to all checks/processes.
    """
    # Identity
    project_name: str
    project: dict
    entity_code: str
    entity_type: str
    entity: dict
    step_name: str
    step_short_name: str
    task_content: str
    task: dict
    user: dict

    # Frozen ShotGrid business fields used by checks
    entity_status: str = ""
    task_status: str = ""
    client_shot_name: str = ""

    # Publish mode
    publish_mode: str = DAILY_MODE

    # Version
    version_num: int = 0
    version_name: str = ""
    version_key: str = ""

    # Tag
    tag_id: Optional[int] = None
    tag_name: str = ""

    # Description
    description: str = ""
    notify_users: list = field(default_factory=list)

    # DCC
    dcc: str = NUKE_DCC
    script_path: Optional[str] = None
    script_modified: bool = False
    nuke_source_mode: str = "current"

    # Preview
    preview_paths: list[str] = field(default_factory=list)
    skip_movie_range_check: bool = False

    # Frame range
    frame_range: Optional[FrameRange] = None

    # Root paths (resolved via old_get_path)
    work_root: str = ""
    publish_root: str = ""

    # Paths (computed)
    version_dir: str = ""
    version_dir_no_num: str = ""
    v_dir_preview: str = ""
    v_dir_nuke: str = ""
    v_dir_json: str = ""

    # ShotGrid
    existing_version_codes: list[str] = field(default_factory=list)
    created_version: Optional[dict] = None

    # Version info JSON
    version_info: dict = field(default_factory=dict)


def build_context(
    task_id: int,
    project_name: str,
    project: dict,
    entity_code: str,
    entity_type: str,
    entity: dict,
    step_name: str,
    step_short_name: str,
    task_content: str,
    task: dict,
    user: dict,
    publish_mode: str = DAILY_MODE,
    version_num: int = 0,
    tag_id: Optional[int] = None,
    tag_name: str = "",
    description: str = "",
    notify_users: Optional[list] = None,
    preview_paths: Optional[list[str]] = None,
    sg_version_codes: Optional[list[str]] = None,
    sg_shot_data: Optional[dict] = None,
    script_path: Optional[str] = None,
    entity_status: str = "",
    task_status: str = "",
    client_shot_name: str = "",
    skip_movie_range_check: bool = False,
    nuke_source_mode: str = "current",
) -> PublishContext:
    """
    Build a fully populated PublishContext with all paths computed.

    Path roots (work_root, publish_root) are resolved internally via
    old_get_path from the ShotGrid task_id. No hardcoded drive letters.

    This is the single entry point for context construction.
    All checks and processes should read from this context, not
    re-derive paths or version numbers.
    """
    work_root, publish_root = _resolve_roots(
        task_id,
        project_name,
    )

    version_key = format_version_key(
        entity_code,
        step_short_name,
        task_content,
    )

    ctx = PublishContext(
        project_name=project_name,
        project=project,
        entity_code=entity_code,
        entity_type=entity_type,
        entity=entity,
        step_name=step_name,
        step_short_name=step_short_name,
        task_content=task_content,
        task=task,
        user=user,
        entity_status=entity_status,
        task_status=task_status,
        client_shot_name=client_shot_name,
        publish_mode=publish_mode,
        version_num=version_num,
        version_key=version_key,
        tag_id=tag_id,
        tag_name=tag_name,
        description=description,
        notify_users=notify_users or [],
        preview_paths=preview_paths or [],
        skip_movie_range_check=skip_movie_range_check,
        existing_version_codes=sg_version_codes or [],
        script_path=script_path,
        nuke_source_mode=nuke_source_mode,
        work_root=work_root,
        publish_root=publish_root,
    )

    # Compute version name
    ctx.version_name = format_version_name(
        entity_code, step_short_name, task_content, version_num
    )

    # Compute paths
    ctx.version_dir = build_version_dir(publish_root, ctx.version_name)
    ctx.version_dir_no_num = build_version_dir_no_num(publish_root, version_key)

    # File paths
    ctx.v_dir_preview = build_preview_path(ctx.version_dir, ctx.version_name)
    ctx.v_dir_nuke = build_nuke_path(ctx.version_dir, ctx.version_name)
    ctx.v_dir_json = build_version_info_path(ctx.version_dir)

    # Frame range
    if sg_shot_data:
        try:
            ctx.frame_range = frame_range_for_step(
                sg_shot_data,
                step_short_name,
            )
        except Exception:
            ctx.frame_range = None

    # Script modified state
    if script_path is None:
        ctx.script_path = get_nuke_script_path()
    else:
        ctx.script_path = script_path
    ctx.script_modified = (
        is_script_modified() if nuke_source_mode == "current" else False
    )

    # Version info dict init
    ctx.version_info = {
        "shot_code": entity_code,
        "version_tag": tag_name,
        "source_nk": ctx.script_path or "",
        "source_preview": preview_paths or [],
    }

    return ctx
