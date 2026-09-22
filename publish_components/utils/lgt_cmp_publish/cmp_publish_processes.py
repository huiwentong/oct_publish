from __future__ import annotations

import hashlib
import os
from typing import Callable, Optional

from .cmp_processes import CmpProcessError, _source_preview_value
from .nuke_scene import (
    execute_in_nuke_main_thread,
    scan_camera_nodes,
    scan_deepread_nodes,
    scan_read_nodes,
)
from .preview import (
    PREVIEW_IMAGE_SEQUENCE,
    PREVIEW_MOVIE,
    PREVIEW_SINGLE_IMAGE,
    analyze_numbered_sequence,
    classify_preview_paths,
)
from .lgt_processes import publish_context


def _normalized(path) -> str:
    return str(path or "").strip().replace("\\", "/")


def _same_path(left: str, right: str) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(
        os.path.abspath(right)
    )


def _require_publish_context(process_data: dict) -> dict:
    context = publish_context(process_data)
    if str(context.get("publish_mode") or "").lower() != "publish":
        raise CmpProcessError("CMP Publish process received a non-Publish context")
    return context


def cmp_publish_cut_duration(shot_data: dict) -> int:
    """Return the inclusive live Cut duration used by strict Publish EXR input."""
    cut_in = shot_data.get("sg_cut_in")
    cut_out = shot_data.get("sg_cut_out")
    if isinstance(cut_in, bool) or isinstance(cut_out, bool):
        raise CmpProcessError("CMP Publish Cut In/Out must be integer frame values")
    try:
        cut_in = int(cut_in)
        cut_out = int(cut_out)
    except (TypeError, ValueError) as exc:
        raise CmpProcessError("CMP Publish Cut In/Out are missing or invalid") from exc
    if cut_out < cut_in:
        raise CmpProcessError("CMP Publish Cut Out must not be before Cut In")
    return cut_out - cut_in + 1


def prepare_cmp_publish_source(
    process_data: dict,
    current_script_path: Optional[Callable[[], Optional[str]]] = None,
    script_save: Optional[Callable[[], object]] = None,
) -> str:
    """Save the frozen current scene, or leave a manual source untouched."""
    context = _require_publish_context(process_data)
    source = _normalized(context.get("script_path"))
    mode = str(context.get("nuke_source_mode") or "current").strip().lower()
    if not source or os.path.splitext(source)[1].lower() != ".nk":
        raise CmpProcessError("CMP Publish source Nuke path is invalid")
    if not os.path.isfile(source):
        raise CmpProcessError("CMP Publish source Nuke file does not exist: {}".format(source))

    if mode == "manual":
        process_data["prepared_nuke_source"] = source
        process_data["nuke_source_saved"] = False
        return source
    if mode != "current":
        raise CmpProcessError("CMP Publish Nuke source mode must be current or manual")

    if current_script_path is None:
        from .nuke_scene import get_nuke_script_path

        current_script_path = get_nuke_script_path
    if script_save is None:
        try:
            import nuke
        except ImportError as exc:
            raise CmpProcessError("Nuke is unavailable; current scene cannot be saved") from exc
        script_save = lambda: execute_in_nuke_main_thread(
            nuke.scriptSave,
            nuke_module=nuke,
        )

    live_source = _normalized(current_script_path())
    if not live_source or not _same_path(live_source, source):
        raise CmpProcessError(
            "Current Nuke scene no longer matches the source frozen on the Form"
        )
    try:
        script_save()
    except Exception as exc:
        raise CmpProcessError("Failed to save current Nuke scene: {}".format(exc)) from exc
    if not os.path.isfile(source):
        raise CmpProcessError("Current Nuke scene was not present after save: {}".format(source))

    process_data["prepared_nuke_source"] = source
    process_data["nuke_source_saved"] = True
    return source


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_cmp_publish_nuke(process_data: dict, file_system) -> str:
    """Copy the prepared .nk into an existing version directory and verify it."""
    context = _require_publish_context(process_data)
    source = _normalized(
        process_data.get("prepared_nuke_source") or context.get("script_path")
    )
    destination = _normalized(context.get("v_dir_nuke"))
    version_dir = _normalized(context.get("version_dir"))
    if not source or not file_system.file_exists(source):
        raise CmpProcessError("CMP Publish source Nuke file is missing: {}".format(source))
    if not destination or not version_dir:
        raise CmpProcessError("CMP Publish Nuke destination is missing")
    if not file_system.dir_exists(version_dir):
        raise CmpProcessError(
            "CMP Publish version directory must exist before copying Nuke: {}".format(
                version_dir
            )
        )
    if file_system.file_exists(destination):
        raise CmpProcessError("CMP Publish Nuke destination already exists: {}".format(destination))

    file_system.copy_file(source, destination, overwrite=False)
    if not file_system.file_exists(destination):
        raise CmpProcessError("CMP Publish Nuke copy was not created: {}".format(destination))
    try:
        if os.path.getsize(source) != os.path.getsize(destination):
            raise CmpProcessError("CMP Publish Nuke copy size verification failed")
        if _sha256(source) != _sha256(destination):
            raise CmpProcessError("CMP Publish Nuke copy hash verification failed")
    except OSError as exc:
        raise CmpProcessError("CMP Publish Nuke copy cannot be verified: {}".format(exc)) from exc

    process_data["published_nk_path"] = destination
    return destination


def scan_cmp_publish_dependencies(
    process_data: dict,
    read_scanner: Callable[[str], dict] = scan_read_nodes,
    deepread_scanner: Callable[[str], dict] = scan_deepread_nodes,
    camera_scanner: Callable[[str], dict] = scan_camera_nodes,
) -> dict:
    """Scan dependencies from the immutable published Nuke copy."""
    _require_publish_context(process_data)
    published_nk = _normalized(process_data.get("published_nk_path"))
    if not published_nk or not os.path.isfile(published_nk):
        raise CmpProcessError("Published Nuke copy must exist before dependency scanning")
    try:
        dependencies = {
            "Read": dict(read_scanner(published_nk) or {}),
            "DeepRead": dict(deepread_scanner(published_nk) or {}),
            "Camera2": dict(camera_scanner(published_nk) or {}),
        }
    except Exception as exc:
        raise CmpProcessError("CMP Publish dependency scan failed: {}".format(exc)) from exc
    process_data.update(dependencies)
    process_data["cmp_dependencies_scanned"] = True
    return dependencies


def _publish_source_exr(context: dict) -> str:
    preview_paths = context.get("preview_paths") or []
    selection = classify_preview_paths(preview_paths)
    if selection.kind == PREVIEW_MOVIE:
        return ""
    if selection.kind not in (PREVIEW_SINGLE_IMAGE, PREVIEW_IMAGE_SEQUENCE):
        raise CmpProcessError("CMP Publish preview must be one MOV or one EXR sequence")
    if any(os.path.splitext(path)[1].lower() != ".exr" for path in selection.preview_paths):
        raise CmpProcessError("CMP Publish image source must contain EXR files only")

    frame_range = context.get("frame_range") or {}
    expected_first = frame_range.get("cut_in")
    expected_last = frame_range.get("cut_out")
    try:
        analysis = analyze_numbered_sequence(
            selection.preview_paths,
            expected_first=expected_first,
            expected_last=expected_last,
        )
    except Exception as exc:
        raise CmpProcessError("CMP Publish EXR sequence cannot be resolved: {}".format(exc)) from exc
    if not analysis.matches_expected_range:
        raise CmpProcessError("CMP Publish EXR sequence no longer matches the frozen Cut range")
    return analysis.pattern


def build_cmp_publish_version_info(process_data: dict) -> dict:
    """Build the Publish JSON contract without writing any file."""
    context = _require_publish_context(process_data)
    if process_data.get("cmp_dependencies_scanned") is not True:
        raise CmpProcessError("CMP Publish dependencies must be scanned before version_info")
    source_nk = _normalized(context.get("script_path"))
    preview_paths = [
        _normalized(path)
        for path in context.get("preview_paths") or []
        if _normalized(path)
    ]
    tag_name = str(context.get("tag_name") or "").strip()
    shot_code = str(context.get("entity_code") or "").strip()
    if not source_nk or not preview_paths or not tag_name or not shot_code:
        raise CmpProcessError("CMP Publish version_info context is incomplete")

    return {
        "r_daily_src": None,
        "source_nk": source_nk,
        "source_exr": _publish_source_exr(context),
        "thumbnail_png": _normalized(process_data.get("source_thumbnail_png")),
        "source_preview": _source_preview_value(preview_paths),
        "publish_mode": "Publish",
        "shot_code": shot_code,
        "version_tag": tag_name,
        "r_daily_dst": None,
        "Read": dict(process_data.get("Read") or {}),
        "DeepRead": dict(process_data.get("DeepRead") or {}),
        "Camera2": dict(process_data.get("Camera2") or {}),
    }


def write_cmp_publish_version_info(process_data: dict, file_system) -> str:
    """Atomically write JSON only after Nuke and preview outputs both exist."""
    context = _require_publish_context(process_data)
    destination = _normalized(context.get("v_dir_json"))
    published_nk = _normalized(process_data.get("published_nk_path"))
    published_preview = _normalized(process_data.get("published_preview_path"))
    if not destination:
        raise CmpProcessError("CMP Publish version_info destination is missing")
    if not file_system.file_exists(published_nk):
        raise CmpProcessError("CMP Publish Nuke output must exist before version_info")
    if not file_system.file_exists(published_preview):
        raise CmpProcessError("CMP Publish preview output must exist before version_info")

    data = build_cmp_publish_version_info(process_data)
    file_system.write_json(destination, data, overwrite=False, ensure_ascii=True)
    if not file_system.file_exists(destination):
        raise CmpProcessError("CMP Publish version_info.json was not created")
    if file_system.read_json(destination) != data:
        raise CmpProcessError("CMP Publish version_info.json verification failed")
    process_data["version_info"] = data
    process_data["published_version_info"] = destination
    return destination


def create_cmp_publish_shotgrid_version(
    process_data: dict,
    file_system,
    sg,
    frame_probe: Callable[[str], int],
    upload_movie: str,
) -> dict:
    """Create/upload a CMP Publish Version without creating a Daily Playlist."""
    context = _require_publish_context(process_data)
    if process_data.get("created_version"):
        raise CmpProcessError("CMP Publish ShotGrid Version was already completed")
    orphaned = process_data.get("orphaned_version")
    if orphaned:
        raise CmpProcessError(
            "A previous upload attempt already created ShotGrid Version {}; "
            "review it before retrying".format(orphaned.get("id") or "<unknown>")
        )

    published_nk = _normalized(process_data.get("published_nk_path"))
    published_preview = _normalized(process_data.get("published_preview_path"))
    published_json = _normalized(process_data.get("published_version_info"))
    upload_path = _normalized(upload_movie)
    required = {
        "published Nuke": published_nk,
        "published preview": published_preview,
        "version_info.json": published_json,
        "ShotGrid upload movie": upload_path,
    }
    for label, path in required.items():
        if not path or not file_system.file_exists(path):
            raise CmpProcessError("CMP Publish {} is missing: {}".format(label, path))

    expected_nk = _normalized(context.get("v_dir_nuke"))
    expected_preview = _normalized(context.get("v_dir_preview"))
    expected_json = _normalized(context.get("v_dir_json"))
    for label, actual, expected in (
        ("Nuke", published_nk, expected_nk),
        ("preview", published_preview, expected_preview),
        ("version_info", published_json, expected_json),
    ):
        if not expected or not _same_path(actual, expected):
            raise CmpProcessError(
                "CMP Publish {} output does not match the frozen destination".format(label)
            )

    tag_id = context.get("tag_id")
    tag_name = str(context.get("tag_name") or "").strip()
    if not tag_id or not tag_name:
        raise CmpProcessError("CMP Publish tag is missing")
    try:
        version_num = int(context.get("version_num"))
    except (TypeError, ValueError) as exc:
        raise CmpProcessError("CMP Publish version number is invalid") from exc
    try:
        frame_count = int(frame_probe(published_preview) or 0)
    except Exception as exc:
        raise CmpProcessError("CMP Publish preview frame probe failed: {}".format(exc)) from exc

    data = {
        "project": context.get("project"),
        "entity": context.get("entity"),
        "sg_task": context.get("task"),
        "code": context.get("version_name"),
        "description": context.get("description") or "",
        "user": context.get("user"),
        "sg_version_type": "Publish",
        "tag_list": [tag_name],
        "created_by": context.get("user"),
        "client_code": "",
        "sg_version_number": "{:03d}".format(version_num),
        "sg_path_to_movie": published_preview,
        "sg_path_to_geometry": published_nk,
    }
    if frame_count:
        data["frame_count"] = frame_count

    try:
        version = sg.create("Version", data)
    except Exception as exc:
        raise CmpProcessError("CMP Publish ShotGrid Version creation failed: {}".format(exc)) from exc
    if not version or not version.get("id"):
        raise CmpProcessError("ShotGrid did not return a CMP Publish Version")

    try:
        sg.upload(
            "Version",
            version["id"],
            upload_path,
            "sg_uploaded_movie",
            display_name=os.path.basename(upload_path),
        )
    except Exception as exc:
        process_data["orphaned_version"] = version
        process_data.pop("created_version", None)
        raise CmpProcessError(
            "CMP Publish Version {} was created but preview upload failed: {}".format(
                version["id"], exc
            )
        ) from exc

    process_data["created_version"] = version
    process_data["preview_duration"] = frame_count
    process_data.pop("orphaned_version", None)
    return version


def lock_cmp_publish_version(process_data: dict, file_system, locker) -> None:
    """Lock a complete CMP Publish version after files and SG upload succeed."""
    context = _require_publish_context(process_data)
    if process_data.get("orphaned_version"):
        raise CmpProcessError("CMP Publish has an orphaned ShotGrid Version; refusing to lock")
    if not process_data.get("created_version"):
        raise CmpProcessError("CMP Publish ShotGrid Version/upload is incomplete")

    required = {
        "published Nuke": process_data.get("published_nk_path"),
        "published preview": process_data.get("published_preview_path"),
        "version_info.json": process_data.get("published_version_info"),
    }
    for label, value in required.items():
        path = _normalized(value)
        if not path or not file_system.file_exists(path):
            raise CmpProcessError("CMP Publish {} is missing; refusing to lock".format(label))

    publish_root = _normalized(context.get("publish_root"))
    version_dir = _normalized(context.get("version_dir"))
    if not publish_root or not version_dir or not file_system.dir_exists(version_dir):
        raise CmpProcessError("CMP Publish lock paths are incomplete")
    try:
        locker(publish_root)
        locker(version_dir, True)
    except Exception as exc:
        process_data.pop("version_locked", None)
        raise CmpProcessError("CMP Publish ACL lock failed: {}".format(exc)) from exc
    process_data["version_locked"] = True


def version_up_cmp_workfile(
    process_data: dict,
    file_system,
    current_script_path: Optional[Callable[[], Optional[str]]] = None,
    open_script: Optional[Callable[[str], object]] = None,
) -> Optional[str]:
    """Copy/open the next current workfile only after a complete locked Publish."""
    context = _require_publish_context(process_data)
    mode = str(context.get("nuke_source_mode") or "current").strip().lower()
    if mode != "current":
        if mode != "manual":
            raise CmpProcessError("CMP Publish Nuke source mode must be current or manual")
    if process_data.get("version_locked") is not True:
        raise CmpProcessError("CMP Publish version must be locked before workfile version-up")
    if not process_data.get("created_version") or process_data.get("orphaned_version"):
        raise CmpProcessError("CMP Publish ShotGrid completion is invalid for version-up")
    if mode == "manual":
        process_data["workfile_version_up_skipped"] = True
        process_data["workfile_version_up_reason"] = "manual source"
        return None

    source = _normalized(context.get("script_path"))
    version_key = str(context.get("version_key") or "").strip()
    try:
        published_num = int(context.get("version_num"))
    except (TypeError, ValueError) as exc:
        raise CmpProcessError("CMP Publish version number is invalid for version-up") from exc
    if not source or not file_system.file_exists(source):
        raise CmpProcessError("CMP Publish current workfile is missing: {}".format(source))
    if not version_key or published_num < 1 or published_num >= 999:
        raise CmpProcessError("CMP Publish cannot create the next workfile version")

    if current_script_path is None:
        from .nuke_scene import get_nuke_script_path

        current_script_path = get_nuke_script_path
    live_source = _normalized(current_script_path())
    if not live_source or not _same_path(live_source, source):
        raise CmpProcessError(
            "Current Nuke scene changed after Publish; refusing automatic version-up"
        )

    next_path = _normalized(
        os.path.join(
            os.path.dirname(source),
            "{}.v{:03d}.nk".format(version_key, published_num + 1),
        )
    )
    if file_system.file_exists(next_path):
        raise CmpProcessError(
            "Next Nuke workfile already exists; refusing to overwrite: {}".format(next_path)
        )
    file_system.copy_file(source, next_path, overwrite=False)
    if not file_system.file_exists(next_path):
        raise CmpProcessError("Next Nuke workfile was not created: {}".format(next_path))
    try:
        if os.path.getsize(source) != os.path.getsize(next_path) or _sha256(source) != _sha256(next_path):
            raise CmpProcessError("Next Nuke workfile copy verification failed")
    except OSError as exc:
        raise CmpProcessError("Next Nuke workfile cannot be verified: {}".format(exc)) from exc

    process_data["version_up_candidate"] = next_path
    if open_script is None:
        try:
            import nuke
        except ImportError as exc:
            raise CmpProcessError("Nuke is unavailable; next workfile cannot be opened") from exc
        open_script = lambda path: execute_in_nuke_main_thread(
            nuke.scriptOpen,
            path,
            nuke_module=nuke,
        )
    try:
        open_script(next_path)
    except Exception as exc:
        raise CmpProcessError(
            "Next workfile was created but Nuke could not open it: {}".format(exc)
        ) from exc
    process_data["version_up_workfile"] = next_path
    process_data.pop("version_up_candidate", None)
    return next_path
