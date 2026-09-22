from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .constants import DAILY_MODE, PUBLISH_MODE, SUBMIT_MODE
from .context import PublishContext, build_context
from .errors import PublishError
from .nuke_scene import get_nuke_script_path
from .modes import validate_publish_mode
from .shotgun import ShotGridReader


PUBLISH_CONTEXT_KEY = "publish_context"
VALID_PUBLISH_MODES = (DAILY_MODE, SUBMIT_MODE, PUBLISH_MODE)


class FormContractError(PublishError):
    """Raised when submitted Form data cannot form a publish context."""


def localize_notify_label(parent: Any, label_type: Any = None) -> bool:
    """Translate the common Form's Notify label for LG/CMP only."""
    if label_type is None:
        from qtpy import QtWidgets

        label_type = QtWidgets.QLabel
    changed = False
    for label in parent.findChildren(label_type):
        if str(label.text()).strip() == "Notify:":
            label.setText("通知人员：")
            changed = True
    return changed


def reset_nuke_submit_requirements(interface: Any) -> None:
    """Reset mutable submit_form to the one DCC input required by the UI."""
    interface.submit_form.clear()
    interface.submit_form["nk_file"] = True


def _normalized_path(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() == "default":
        return ""
    return text.replace("\\", "/")


def _entity_ref(value: Any, label: str) -> dict:
    if hasattr(value, "tiny_raw"):
        value = value.tiny_raw()
    if not isinstance(value, dict):
        raise FormContractError("{} must be a ShotGrid entity reference".format(label))
    entity_id = value.get("id")
    entity_type = value.get("type")
    if not entity_id or not entity_type:
        raise FormContractError("{} is missing type or id".format(label))
    return {"type": entity_type, "id": entity_id}


def _entity_attr(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    try:
        return getattr(value, name)
    except (AttributeError, TypeError):
        return default


@dataclass(frozen=True)
class FormSubmission:
    """Validated values collected from the common publish Form."""

    publish_mode: str
    version_num: int
    tag_id: int
    description: str
    preview_paths: tuple[str, ...]
    notify_users: tuple[dict, ...]
    script_path: str
    nuke_source_mode: str = "current"
    skip_movie_range_check: bool = False

    @classmethod
    def from_process_data(
        cls,
        process_data: dict,
        script_path: Optional[str] = None,
    ) -> "FormSubmission":
        mode = str(process_data.get("publish_type") or "").strip()
        if mode not in VALID_PUBLISH_MODES:
            raise FormContractError("Unsupported publish mode: {}".format(mode or "<empty>"))

        version_num = process_data.get("version_num")
        if isinstance(version_num, bool) or not isinstance(version_num, int):
            raise FormContractError("Version number must be an integer")
        if version_num < 1 or version_num > 999:
            raise FormContractError("Version number must be between 1 and 999")

        tag_id = process_data.get("publish_tag_id")
        if isinstance(tag_id, bool) or not isinstance(tag_id, int) or tag_id <= 0:
            raise FormContractError("A real publish tag is required")

        description = str(process_data.get("comment") or "").strip()
        if len(description) < 15:
            raise FormContractError("Publish comment must contain at least 15 characters")

        raw_previews = process_data.get("preview_paths") or []
        if isinstance(raw_previews, (str, Path)):
            raw_previews = [raw_previews]
        preview_paths = tuple(
            path for path in (_normalized_path(item) for item in raw_previews) if path
        )
        if not preview_paths:
            raise FormContractError("At least one preview path is required")

        raw_notify = process_data.get("notify") or []
        if not isinstance(raw_notify, (list, tuple)):
            raise FormContractError("Notify users must be a list")
        notify_users = []
        seen_notify_ids = set()
        for user in raw_notify:
            ref = _entity_ref(user, "Notify user")
            key = (ref["type"], ref["id"])
            if key not in seen_notify_ids:
                notify_users.append(ref)
                seen_notify_ids.add(key)

        resolved_script = _normalized_path(script_path)
        if not resolved_script:
            resolved_script = _normalized_path(get_nuke_script_path())
        if not resolved_script:
            raise FormContractError("The current Nuke script must be saved before publishing")
        if Path(resolved_script).suffix.lower() != ".nk":
            raise FormContractError("The selected Nuke workfile must end with .nk")

        nuke_source_mode = str(
            process_data.get("nuke_source_mode") or "current"
        ).strip().lower()
        if nuke_source_mode not in ("current", "manual"):
            raise FormContractError("Nuke source mode must be current or manual")

        skip_movie_range_check = process_data.get("skip_movie_range_check", False)
        if not isinstance(skip_movie_range_check, bool):
            raise FormContractError("MOV range skip option must be a boolean")

        return cls(
            publish_mode=mode,
            version_num=version_num,
            tag_id=tag_id,
            description=description,
            preview_paths=preview_paths,
            notify_users=tuple(notify_users),
            script_path=resolved_script,
            nuke_source_mode=nuke_source_mode,
            skip_movie_range_check=skip_movie_range_check,
        )


@dataclass(frozen=True)
class TaskSnapshot:
    task_id: int
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
    entity_status: str = ""
    task_status: str = ""


@dataclass(frozen=True)
class FormContract:
    """Stable boundary passed from the common Form to check/process components."""

    submit_form: dict
    process_updates: dict
    context: PublishContext

    def apply(self, submit_form: dict, process_data: dict) -> None:
        submit_form.clear()
        submit_form.update(self.submit_form)
        process_data.update(self.process_updates)


def task_snapshot(task_entity: Any, user: Any) -> TaskSnapshot:
    project_obj = _entity_attr(task_entity, "project")
    entity_obj = _entity_attr(task_entity, "entity")
    step_obj = _entity_attr(task_entity, "step")
    task_ref = _entity_ref(task_entity, "Task")
    project_ref = _entity_ref(project_obj, "Project")
    entity_ref = _entity_ref(entity_obj, "Entity")
    user_ref = _entity_ref(user, "User")

    project_name = (
        _entity_attr(project_obj, "code")
        or _entity_attr(project_obj, "name")
        or ""
    )
    entity_code = _entity_attr(entity_obj, "code") or _entity_attr(entity_obj, "name") or ""
    step_short_name = _entity_attr(step_obj, "short_name") or ""
    step_name = _entity_attr(step_obj, "code") or _entity_attr(step_obj, "name") or step_short_name
    task_content = _entity_attr(task_entity, "content") or ""
    if not all((project_name, entity_code, step_short_name, task_content)):
        raise FormContractError("Task metadata is incomplete for publish context")

    return TaskSnapshot(
        task_id=task_ref["id"],
        project_name=str(project_name),
        project=project_ref,
        entity_code=str(entity_code),
        entity_type=entity_ref["type"],
        entity=entity_ref,
        step_name=str(step_name),
        step_short_name=str(step_short_name),
        task_content=str(task_content),
        task=task_ref,
        user=user_ref,
        entity_status=str(_entity_attr(entity_obj, "sg_status_list") or ""),
        task_status=str(_entity_attr(task_entity, "sg_status_list") or ""),
    )


def build_form_contract(
    process_data: dict,
    snapshot: TaskSnapshot,
    tag: dict,
    version_rows: list[dict],
    shot_data: dict,
    script_path: Optional[str] = None,
    context_builder: Callable[..., PublishContext] = build_context,
) -> FormContract:
    submission = FormSubmission.from_process_data(process_data, script_path)
    validate_publish_mode(snapshot.step_short_name, submission.publish_mode)
    tag_ref = _entity_ref(tag, "Publish tag")
    tag_name = str(tag.get("name") or "").strip()
    if tag_ref["id"] != submission.tag_id or not tag_name:
        raise FormContractError("Publish tag data does not match the selected tag")

    version_codes = [
        str(row.get("code"))
        for row in version_rows or []
        if row.get("code")
    ]
    context = context_builder(
        task_id=snapshot.task_id,
        project_name=snapshot.project_name,
        project=snapshot.project,
        entity_code=snapshot.entity_code,
        entity_type=snapshot.entity_type,
        entity=snapshot.entity,
        step_name=snapshot.step_name,
        step_short_name=snapshot.step_short_name,
        task_content=snapshot.task_content,
        task=snapshot.task,
        user=snapshot.user,
        publish_mode=submission.publish_mode,
        version_num=submission.version_num,
        tag_id=submission.tag_id,
        tag_name=tag_name,
        description=submission.description,
        notify_users=list(submission.notify_users),
        preview_paths=list(submission.preview_paths),
        sg_version_codes=version_codes,
        sg_shot_data=shot_data,
        script_path=submission.script_path,
        nuke_source_mode=submission.nuke_source_mode,
        entity_status=snapshot.entity_status,
        task_status=snapshot.task_status,
        client_shot_name=str((shot_data or {}).get("sg_client_shot_name") or ""),
        skip_movie_range_check=submission.skip_movie_range_check,
    )
    context_data = asdict(context)
    submit_form = {
        "nk_file": submission.script_path,
        "publish_type": submission.publish_mode,
        "version_num": submission.version_num,
        "publish_tag_id": submission.tag_id,
        "publish_tag": {"type": "Tag", "id": submission.tag_id, "name": tag_name},
        "comment": submission.description,
        "preview_paths": list(submission.preview_paths),
    }
    process_updates = {
        PUBLISH_CONTEXT_KEY: context_data,
        "version_name": context.version_name,
        "version_key": context.version_key,
        "version_dir": context.version_dir,
        "existing_version_codes": version_codes,
        "shot_data": dict(shot_data or {}),
        "skip_movie_range_check": submission.skip_movie_range_check,
        "nuke_source_mode": submission.nuke_source_mode,
    }
    return FormContract(submit_form, process_updates, context)


def bind_interface_form(
    interface: Any,
    reader: Optional[ShotGridReader] = None,
    context_builder: Callable[..., PublishContext] = build_context,
    script_path: Optional[str] = None,
) -> FormContract:
    """Build and attach the common LG/CMP Form contract to an interface."""
    if not interface.process_data:
        raise FormContractError("Interface process_data is empty")
    user = interface.process_data.get("user")
    snapshot = task_snapshot(interface.task_entity, user)
    if reader is None:
        from publish_core.database.core import FastSg

        reader = ShotGridReader(FastSg().client)

    tag = reader.tag(interface.process_data.get("publish_tag_id"))
    version_rows = reader.task_versions(snapshot.project, snapshot.task)
    shot_data = reader.shot_cut_info(snapshot.entity)
    selected_script = script_path or interface.submit_form.get("nk_file")
    contract = build_form_contract(
        interface.process_data,
        snapshot,
        tag,
        version_rows,
        shot_data,
        selected_script,
        context_builder,
    )
    contract.apply(interface.submit_form, interface.process_data)
    return contract
