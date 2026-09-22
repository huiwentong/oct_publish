from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime, timezone
from typing import Callable, Optional

from .preview import PREVIEW_EXR_PNG, PREVIEW_MOVIE, classify_preview_paths


class LgtProcessError(RuntimeError):
    """A user-facing failure raised by an LGT publish process."""


def validate_uat_target(
    process_data: dict,
    project_id: int,
    entity_id: int,
    task_id: int,
) -> None:
    """Block all publish side effects unless the frozen context is the UAT Task."""
    context = publish_context(process_data)
    actual = (
        (context.get("project") or {}).get("id"),
        (context.get("entity") or {}).get("id"),
        (context.get("task") or {}).get("id"),
    )
    expected = (project_id, entity_id, task_id)
    if actual != expected:
        raise LgtProcessError(
            "UAT safety lock blocked this publish. "
            "Expected Project/Shot/Task IDs {}, got {}.".format(expected, actual)
        )
    publish_root = str(context.get("publish_root") or "").replace("\\", "/").lower()
    expected_root = "i:/projects/tdtest/shot/s57/s570320/lgt"
    if publish_root.rstrip("/") != expected_root:
        raise LgtProcessError(
            "UAT safety lock blocked unexpected publish root: {}".format(publish_root)
        )


def publish_context(process_data: dict) -> dict:
    context = process_data.get("publish_context")
    if not isinstance(context, dict):
        raise LgtProcessError("PublishContext is missing")
    return context


def create_version_dirs(process_data: dict, file_system) -> str:
    """Create a new version/preview directory without overwriting a version."""
    context = publish_context(process_data)
    publish_root = str(context.get("publish_root") or "")
    version_dir = str(context.get("version_dir") or "")
    preview_path = str(context.get("v_dir_preview") or "")
    preview_dir = os.path.dirname(preview_path)
    if not all((publish_root, version_dir, preview_dir)):
        raise LgtProcessError("Publish output paths are incomplete")
    if file_system.dir_exists(version_dir):
        raise LgtProcessError(
            "Version directory already exists; refusing to overwrite: {}".format(
                version_dir
            )
        )
    file_system.ensure_dir(publish_root)
    file_system.ensure_dir(preview_dir)
    if not file_system.dir_exists(preview_dir):
        raise LgtProcessError(
            "Failed to create version preview directory: {}".format(preview_dir)
        )
    process_data["created_version_dir"] = version_dir
    return preview_dir


def preview_image_inputs(preview_paths: list[str]) -> list[str]:
    """Return image inputs for MOV generation, excluding the EXR+PNG thumbnail."""
    selection = classify_preview_paths(preview_paths)
    if selection.kind == PREVIEW_EXR_PNG:
        return [
            path for path in selection.preview_paths
            if os.path.splitext(path)[1].lower() == ".exr"
        ]
    return list(selection.preview_paths)


def preview_duration(context: dict, image_paths: list[str], shot_data: dict) -> int:
    """Match legacy LGT duration priority while accepting current step aliases."""
    entity = context.get("entity") or {}
    step = str(context.get("step_short_name") or "").strip().lower()
    cut_duration = (shot_data or {}).get("sg_cut_duration")
    if (
        entity.get("type") == "Shot"
        and step in {"ef", "efx", "lg", "lgt", "cm", "cmp"}
        and cut_duration
    ):
        return int(cut_duration)
    return len(image_paths)


def copy_or_create_preview(
    process_data: dict,
    file_system,
    movie_creator: Callable[[list[str], str, int], None],
) -> str:
    """Copy a MOV or generate one from the selected LGT image input."""
    context = publish_context(process_data)
    selection = classify_preview_paths(context.get("preview_paths") or [])
    destination = str(context.get("v_dir_preview") or "")
    if not destination:
        raise LgtProcessError("Published preview path is missing")
    if not selection.preview_paths:
        raise LgtProcessError("No preview media was selected")

    if selection.kind == PREVIEW_MOVIE:
        file_system.copy_file(selection.preview_paths[0], destination)
    else:
        image_paths = preview_image_inputs(list(selection.preview_paths))
        if not image_paths:
            raise LgtProcessError("No image input is available for MOV generation")
        duration = preview_duration(
            context,
            image_paths,
            process_data.get("shot_data") or {},
        )
        movie_creator(image_paths, destination, duration)

    if not file_system.file_exists(destination):
        raise LgtProcessError(
            "Published preview MOV was not created: {}".format(destination)
        )
    process_data["published_preview_path"] = destination
    return destination


def copy_thumbnail(process_data: dict, file_system) -> Optional[str]:
    """Copy the PNG in an EXR+PNG pair; no PNG is a successful no-op."""
    context = publish_context(process_data)
    selection = classify_preview_paths(context.get("preview_paths") or [])
    png_paths = [
        path for path in selection.preview_paths
        if os.path.splitext(path)[1].lower() == ".png"
    ]
    if not png_paths:
        process_data["published_thumbnail_path"] = ""
        return None
    source = png_paths[0]
    thumbnail_dir = os.path.join(str(context.get("version_dir") or ""), "thumbnail")
    destination = os.path.join(thumbnail_dir, os.path.basename(source))
    file_system.copy_file(source, destination)
    if not file_system.file_exists(destination):
        raise LgtProcessError(
            "Published thumbnail was not created: {}".format(destination)
        )
    process_data["published_thumbnail_path"] = destination
    return destination


def _utc_date(now: Optional[datetime] = None) -> str:
    value = now or datetime.now(timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%d")


def _tag_name(context: dict) -> str:
    tag_id = context.get("tag_id")
    tag_name = str(context.get("tag_name") or "").strip()
    if not tag_id or not tag_name:
        raise LgtProcessError("Publish tag is missing")
    return tag_name


def _local_temp_root() -> str:
    """Return a local Windows temp root and explicitly reject W:/UNC paths."""
    temp_root = os.path.abspath(tempfile.gettempdir())
    normalized = temp_root.replace("\\", "/")
    drive, _tail = os.path.splitdrive(temp_root)
    if not temp_root or normalized.startswith("//") or drive.upper() == "W:":
        raise LgtProcessError(
            "ShotGrid upload temp must be local Windows TEMP, got: {}".format(
                temp_root
            )
        )
    return temp_root


def cleanup_sg_upload_movie(process_data: dict) -> None:
    """Remove only the per-run local temp directory created by this publisher."""
    temp_dir = str(process_data.pop("sg_upload_temp_dir", "") or "")
    process_data.pop("sg_upload_movie", None)
    if not temp_dir:
        return

    temp_root = os.path.realpath(_local_temp_root())
    candidate = os.path.realpath(temp_dir)
    try:
        is_child = (
            candidate != temp_root
            and os.path.commonpath([temp_root, candidate]) == temp_root
        )
    except ValueError:
        is_child = False
    if not is_child:
        raise LgtProcessError(
            "Refusing to clean an unsafe ShotGrid temp path: {}".format(temp_dir)
        )
    if os.path.isdir(candidate):
        shutil.rmtree(candidate)


def prepare_sg_upload_movie(
    process_data: dict,
    file_system,
    converter: Callable[[str, str, str], bool],
) -> str:
    """Convert the final MOV before creating the SG Version entity."""
    context = publish_context(process_data)
    source = str(
        process_data.get("published_preview_path")
        or context.get("v_dir_preview")
        or ""
    )
    if not file_system.file_exists(source):
        raise LgtProcessError("Published preview MOV does not exist: {}".format(source))
    version_name = str(context.get("version_name") or "").strip()
    if not version_name:
        raise LgtProcessError("Version name is missing for ShotGrid upload")

    temp_dir = tempfile.mkdtemp(
        prefix="oct_publish_{}_".format(version_name),
        dir=_local_temp_root(),
    )
    destination = os.path.join(temp_dir, version_name + ".sg.mov")
    process_data["sg_upload_temp_dir"] = temp_dir
    process_data["sg_upload_movie"] = destination
    try:
        if not converter(source, destination, str(context.get("dcc") or "Nuke")):
            raise LgtProcessError(
                "Failed to convert MOV for ShotGrid: {}".format(source)
            )
        if not file_system.file_exists(destination):
            raise LgtProcessError(
                "ShotGrid-compatible MOV was not created: {}".format(destination)
            )
        return destination
    except Exception:
        cleanup_sg_upload_movie(process_data)
        raise


def create_shotgrid_version(
    process_data: dict,
    sg,
    frame_probe: Callable[[str], int],
    upload_movie: str,
    now: Optional[datetime] = None,
) -> dict:
    """Create the Version, upload its MOV, and connect the daily Playlist."""
    context = publish_context(process_data)
    preview_path = str(
        process_data.get("published_preview_path")
        or context.get("v_dir_preview")
        or ""
    )
    frame_count = int(frame_probe(preview_path) or 0)
    data = {
        "project": context.get("project"),
        "entity": context.get("entity"),
        "sg_task": context.get("task"),
        "code": context.get("version_name"),
        "description": context.get("description") or "",
        "user": context.get("user"),
        "sg_version_type": context.get("publish_mode"),
        "tag_list": [_tag_name(context)],
        "created_by": context.get("user"),
        "client_code": "",
        # This ShotGrid site's Version.sg_version_number is a text field.
        # Keep the same zero-padded string convention used by the framework's
        # existing EFX publisher (for example, "012" rather than integer 12).
        "sg_version_number": "{:03d}".format(int(context.get("version_num"))),
        "sg_path_to_movie": preview_path,
    }
    if frame_count:
        data["frame_count"] = frame_count
    version = sg.create("Version", data)
    if not version or not version.get("id"):
        raise LgtProcessError("ShotGrid did not return a created Version")
    process_data["created_version"] = version
    process_data["preview_duration"] = frame_count

    # shotgun_api3 3.3.1 encodes ``path`` to bytes before deriving its default
    # display name under Python 3, which produces names such as ``b'file.mov'``.
    # Pass the intended Unicode filename explicitly.
    sg.upload(
        "Version",
        version["id"],
        upload_movie,
        "sg_uploaded_movie",
        display_name=os.path.basename(upload_movie),
    )
    if str(context.get("publish_mode") or "").lower() == "dailies":
        playlist_code = "{}_Dailies_{}".format(
            str(context.get("project_name") or "").upper(),
            _utc_date(now),
        )
        filters = [
            ["project", "is", context.get("project")],
            ["code", "is", playlist_code],
        ]
        playlist = sg.find_one("Playlist", filters, ["id", "code"])
        if not playlist:
            playlist = sg.create(
                "Playlist",
                {"project": context.get("project"), "code": playlist_code},
            )
        if not playlist or not playlist.get("id"):
            raise LgtProcessError("ShotGrid daily Playlist could not be resolved")
        sg.create(
            "PlaylistVersionConnection",
            {
                "playlist": {"type": "Playlist", "id": playlist["id"]},
                "version": {"type": "Version", "id": version["id"]},
            },
        )
        process_data["daily_playlist"] = playlist
    return version


def lock_version(process_data: dict, locker: Callable[..., None]) -> None:
    """Lock the publish root and recursively lock the completed version."""
    context = publish_context(process_data)
    publish_root = str(context.get("publish_root") or "")
    version_dir = str(context.get("version_dir") or "")
    if not all((publish_root, version_dir)):
        raise LgtProcessError("Publish lock paths are incomplete")
    locker(publish_root)
    locker(version_dir, True)
    process_data["version_locked"] = True
