from __future__ import annotations

from typing import Any, Optional

from .errors import ShotGridError


VERSION_FIELDS = [
    "code", "user", "created_at", "description",
    "sg_version_type", "sg_version_number",
]

CUT_FIELDS = [
    "sg_ani_cut_in", "sg_ani_cut_out", "sg_head_in", "sg_tail_out",
    "sg_cut_duration", "sg_client_shot_name", "code",
]


def query_task_versions(sg, project: dict, task: dict) -> list[dict]:
    """
    Query all ShotGrid Versions for a task.

    Returns list of version dicts with fields:
      code, user, created_at, description, sg_version_type, sg_version_number
    """
    try:
        versions = sg.find(
            "Version",
            [
                ["project", "is", project],
                ["sg_task", "is", task],
                ["sg_status_list", "is_not", "omt"],
            ],
            VERSION_FIELDS,
        )
        return list(versions or [])
    except Exception as e:
        raise ShotGridError(f"Failed to query task versions: {e}") from e


def query_all_task_versions(sg, project: dict, task: dict) -> list[dict]:
    """
    Query ALL ShotGrid Versions for a task (including omitted).
    """
    try:
        versions = sg.find(
            "Version",
            [
                ["project", "is", project],
                ["sg_task", "is", task],
            ],
            VERSION_FIELDS,
        )
        return list(versions or [])
    except Exception as e:
        raise ShotGridError(f"Failed to query all task versions: {e}") from e


def query_shot_cut_info(sg, shot: dict) -> dict:
    """
    Query cut information for a shot.

    Returns dict with: sg_ani_cut_in, sg_ani_cut_out, sg_head_in, sg_tail_out, sg_cut_duration
    """
    try:
        result = sg.find_one(
            "Shot",
            [["id", "is", shot["id"]]],
            CUT_FIELDS,
        )
        return result or {}
    except Exception as e:
        raise ShotGridError(f"Failed to query shot cut info: {e}") from e


def query_daily_playlist(sg, project: dict, today_str: str) -> Optional[dict]:
    """
    Find or query the daily playlist for a given date.

    Returns playlist dict or None if not found.
    """
    try:
        playlists = sg.find(
            "Playlist",
            [
                ["project", "is", project],
                ["code", "contains", today_str],
            ],
            ["id", "code", "versions"],
        )
        if playlists:
            return playlists[0]
        return None
    except Exception as e:
        raise ShotGridError(f"Failed to query daily playlist: {e}") from e


def create_sg_version(
    sg,
    project: dict,
    entity: dict,
    task: dict,
    user: dict,
    code: str,
    description: str,
    publish_mode: str,
    tag_list: list,
    version_num: int,
    sg_path_to_movie: Optional[str] = None,
    sg_path_to_frames: Optional[str] = None,
    frame_count: Optional[int] = None,
    sg_status_list: Optional[str] = None,
) -> dict:
    """
    Create a ShotGrid Version entity.

    Returns the created version dict.
    """
    try:
        data = {
            "project": project,
            "entity": entity,
            "sg_task": task,
            "code": code,
            "description": description,
            "user": user,
            "sg_version_type": publish_mode,
            "tag_list": tag_list,
            "created_by": user,
            "sg_version_number": version_num,
        }

        if sg_path_to_movie:
            data["sg_path_to_movie"] = sg_path_to_movie
        if sg_path_to_frames:
            data["sg_path_to_frames"] = sg_path_to_frames
        if frame_count:
            data["frame_count"] = frame_count
        if sg_status_list:
            data["sg_status_list"] = sg_status_list

        version = sg.create("Version", data)
        return version
    except Exception as e:
        raise ShotGridError(f"Failed to create SG Version: {e}") from e


def upload_preview(sg, version_id: int, preview_path: str) -> None:
    """
    Upload a preview movie to a ShotGrid Version.
    """
    try:
        sg.upload(
            "Version",
            version_id,
            preview_path,
            "sg_uploaded_movie",
        )
    except Exception as e:
        raise ShotGridError(f"Failed to upload preview: {e}") from e


def add_version_to_playlist(sg, playlist_id: int, version: dict) -> None:
    """
    Add a version to a ShotGrid Playlist.
    """
    try:
        existing = sg.find_one(
            "Playlist",
            [["id", "is", playlist_id]],
            ["versions"],
        )
        versions = existing.get("versions", []) if existing else []
        versions.append(version)
        sg.update("Playlist", playlist_id, {"versions": versions})
    except Exception as e:
        raise ShotGridError(f"Failed to add version to playlist: {e}") from e


def query_tag_by_id(sg, tag_id: int) -> dict:
    """
    Query a Tag entity by ID.
    """
    try:
        tag = sg.find_one("Tag", [["id", "is", tag_id]], ["id", "name"])
        if not tag:
            raise ShotGridError("Tag {} was not found".format(tag_id))
        return tag
    except ShotGridError:
        raise
    except Exception as e:
        raise ShotGridError(f"Failed to query Tag {tag_id}: {e}") from e


def query_tags_by_ids(sg, tag_ids: list[int]) -> list[dict]:
    """Query Tag entities once and return them in requested ID order."""
    requested = list(tag_ids)
    if not requested:
        return []
    try:
        rows = sg.find("Tag", [["id", "in", requested]], ["id", "name"])
        by_id = {row["id"]: row for row in rows or []}
        missing = [tag_id for tag_id in requested if tag_id not in by_id]
        if missing:
            raise ShotGridError(
                "Missing ShotGrid Tags: {}".format(
                    ", ".join(str(tag_id) for tag_id in missing)
                )
            )
        return [by_id[tag_id] for tag_id in requested]
    except ShotGridError:
        raise
    except Exception as e:
        raise ShotGridError(f"Failed to query Tags {requested}: {e}") from e


class ShotGridReader:
    """Read-only ShotGrid adapter with an injected API-compatible client."""

    def __init__(self, sg):
        self.sg = sg

    def task_versions(self, project, task, include_omitted=False):
        query = query_all_task_versions if include_omitted else query_task_versions
        return query(self.sg, project, task)

    def task_version_codes(self, project, task, include_omitted=False):
        return [
            row["code"]
            for row in self.task_versions(project, task, include_omitted)
            if row.get("code")
        ]

    def shot_cut_info(self, shot):
        return query_shot_cut_info(self.sg, shot)

    def tag(self, tag_id):
        return query_tag_by_id(self.sg, tag_id)

    def tags(self, tag_ids):
        return query_tags_by_ids(self.sg, tag_ids)
