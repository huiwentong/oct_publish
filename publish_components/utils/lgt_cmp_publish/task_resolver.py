from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


_WORKFILE_RE = re.compile(
    r"^(?P<entity>[^.]+)\."
    r"(?P<step>[^.]+)\."
    r"(?P<task>.+)\."
    r"v(?P<version>\d{3})\.nk$",
    re.IGNORECASE,
)

_PROJECT_PATH_RE = re.compile(
    r"(?:^|/)projects/(?P<project>[^/]+)(?:/|$)",
    re.IGNORECASE,
)

_STEP_ALIASES = {
    "lg": {"lg", "lgt"},
    "lgt": {"lg", "lgt"},
    "cm": {"cm", "cmp"},
    "cmp": {"cm", "cmp"},
}


class TaskResolutionError(RuntimeError):
    """Raised when a workfile cannot be resolved to one unique ShotGrid Task."""


@dataclass(frozen=True)
class ParsedNukeWorkfile:
    """Identity fields parsed from a normalized MK2 Nuke workfile path."""

    script_path: str
    project_name: Optional[str]
    entity_code: str
    step_hint: str
    task_content: str
    version_num: int


@dataclass(frozen=True)
class ResolvedTask:
    """A unique ShotGrid task selected from a parsed Nuke workfile."""

    parsed: ParsedNukeWorkfile
    project: dict
    entity: dict
    task: dict
    step: dict

    @property
    def task_id(self) -> int:
        return int(self.task["id"])

    @property
    def step_short_name(self) -> str:
        return str(self.step.get("short_name") or "").lower()


def parse_nuke_workfile(
    script_path: str,
    project_name: Optional[str] = None,
) -> ParsedNukeWorkfile:
    """Parse ``{entity}.{step}.{task}.vNNN.nk`` without external side effects."""
    normalized = str(script_path or "").strip().replace("\\", "/")
    if not normalized or normalized.lower() == "root":
        raise TaskResolutionError("The current Nuke script has not been saved.")

    file_name = normalized.rsplit("/", 1)[-1]
    match = _WORKFILE_RE.fullmatch(file_name)
    if not match:
        raise TaskResolutionError(
            "The Nuke filename must match "
            "{{entity}}.{{step}}.{{task}}.vNNN.nk: {}".format(file_name)
        )

    resolved_project = str(project_name or "").strip() or None
    if resolved_project is None:
        path_match = _PROJECT_PATH_RE.search(normalized)
        if path_match:
            resolved_project = path_match.group("project")

    return ParsedNukeWorkfile(
        script_path=normalized,
        project_name=resolved_project,
        entity_code=match.group("entity"),
        step_hint=match.group("step").lower(),
        task_content=match.group("task"),
        version_num=int(match.group("version")),
    )


def resolve_task_from_path(
    script_path: str,
    sg: Any = None,
    project_name: Optional[str] = None,
) -> ResolvedTask:
    """Resolve an MK2 Nuke workfile to exactly one ShotGrid Task."""
    parsed = parse_nuke_workfile(script_path, project_name=project_name)
    if not parsed.project_name:
        raise TaskResolutionError(
            "The project cannot be determined from the current Nuke path."
        )

    if sg is None:
        from publish_core.database.core import FastSg

        sg = FastSg().client

    projects = sg.find(
        "Project",
        [],
        ["id", "name", "code"],
    )
    project_key = parsed.project_name.lower()
    projects = [
        project
        for project in projects
        if project_key
        in {
            str(project.get("name") or "").lower(),
            str(project.get("code") or "").lower(),
        }
    ]
    project = _require_unique(projects, "project", parsed.project_name)

    entities = sg.find(
        "Shot",
        [
            ["project", "is", project],
            ["code", "is", parsed.entity_code],
        ],
        ["id", "code", "project"],
    )
    entity = _require_unique(entities, "shot", parsed.entity_code)

    tasks = sg.find(
        "Task",
        [["entity", "is", entity]],
        ["id", "content", "step", "entity", "project", "sg_status_list"],
    )
    task_content = parsed.task_content.lower()
    tasks = [
        task
        for task in tasks
        if str(task.get("content") or "").lower() == task_content
    ]

    step_aliases = _STEP_ALIASES.get(parsed.step_hint, {parsed.step_hint})
    matches = []
    for task in tasks:
        step_link = task.get("step")
        if not step_link or not step_link.get("id"):
            continue
        step = sg.find_one(
            "Step",
            [["id", "is", step_link["id"]]],
            ["id", "code", "short_name", "description"],
        )
        if not step:
            continue
        step_names = {
            str(step.get("code") or "").lower(),
            str(step.get("short_name") or "").lower(),
            str(step.get("description") or "").lower(),
        }
        if step_aliases.intersection(step_names):
            matches.append((task, step))

    if not matches:
        raise TaskResolutionError(
            "No ShotGrid Task matches shot '{}', step '{}', task '{}'.".format(
                parsed.entity_code,
                parsed.step_hint,
                parsed.task_content,
            )
        )
    if len(matches) != 1:
        task_ids = ", ".join(str(item[0].get("id")) for item in matches)
        raise TaskResolutionError(
            "Multiple ShotGrid Tasks match the current Nuke file: {}.".format(
                task_ids
            )
        )

    task, step = matches[0]
    return ResolvedTask(
        parsed=parsed,
        project=project,
        entity=entity,
        task=task,
        step=step,
    )


def _require_unique(items: list, label: str, value: str) -> dict:
    """Return one result or raise a user-readable resolution error."""
    if not items:
        raise TaskResolutionError(
            "No ShotGrid {} matches '{}'.".format(label, value)
        )
    if len(items) != 1:
        ids = ", ".join(str(item.get("id")) for item in items)
        raise TaskResolutionError(
            "Multiple ShotGrid {} records match '{}': {}.".format(
                label,
                value,
                ids,
            )
        )
    return items[0]
