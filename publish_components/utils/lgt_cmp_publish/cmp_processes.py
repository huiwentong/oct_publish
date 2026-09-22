from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile

from .lgt_processes import (
    LgtProcessError,
    copy_or_create_preview,
    create_shotgrid_version,
    create_version_dirs,
    lock_version,
    publish_context,
)


DEFAULT_RVIO = "C:/Program Files/Shotgun/RV-7.7.0/bin/rvio_hw.exe"


class CmpProcessError(LgtProcessError):
    """A user-facing failure raised by a CMP publish process."""


def is_cmp_dailies_context(process_data: dict) -> bool:
    """Return whether a framework process is handling CMP Dailies."""
    context = publish_context(process_data)
    return str(context.get("publish_mode") or "").strip().lower() == "dailies"


def validate_cmp_uat_target(
    process_data: dict,
    project_id: int,
    entity_id: int,
    task_id: int,
) -> None:
    """Allow CMP real processes only for one approved TDTEST task and MOV."""
    context = publish_context(process_data)
    actual = (
        (context.get("project") or {}).get("id"),
        (context.get("entity") or {}).get("id"),
        (context.get("task") or {}).get("id"),
    )
    expected = (project_id, entity_id, task_id)
    if actual != expected:
        raise CmpProcessError(
            "CMP UAT safety lock expected Project/Shot/Task IDs {}, got {}".format(
                expected,
                actual,
            )
        )
    publish_root = str(context.get("publish_root") or "").replace("\\", "/").lower()
    expected_root = "i:/projects/tdtest/shot/s57/s570320/cmp"
    if publish_root.rstrip("/") != expected_root:
        raise CmpProcessError(
            "CMP UAT safety lock blocked unexpected publish root: {}".format(
                publish_root
            )
        )


def _cmp_local_temp_root(temp_root=None) -> str:
    """Resolve a local temp root and reject W:/UNC paths."""
    root = os.path.abspath(temp_root or tempfile.gettempdir())
    normalized = root.replace("\\", "/")
    drive, _tail = os.path.splitdrive(root)
    if not root or normalized.startswith("//") or drive.upper() == "W:":
        raise CmpProcessError(
            "CMP image conversion temp must be local Windows TEMP, got: {}".format(
                root
            )
        )
    return root


def _expanded_image_sources(image_paths: list[str], duration: int) -> list[str]:
    """Repeat review images across duration using the legacy distribution."""
    if not image_paths:
        raise CmpProcessError("CMP image conversion has no source images")
    if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
        raise CmpProcessError("CMP image conversion duration must be positive")
    if len(image_paths) * 2 - 1 <= duration:
        quotient, remainder = divmod(duration, len(image_paths))
        expanded = []
        for index, path in enumerate(image_paths):
            repeat = quotient + (1 if index < remainder else 0)
            expanded.extend([path] * repeat)
        return expanded
    return list(image_paths)


def create_cmp_review_movie(
    image_paths: list[str],
    destination: str,
    duration: int,
    rvio_path: str = DEFAULT_RVIO,
    runner=subprocess.run,
    temp_root=None,
    frame_probe=None,
) -> None:
    """Create a CMP review MOV through RVIO and always clean local temp."""
    sources = _expanded_image_sources(list(image_paths), duration)
    for source in sources:
        if not os.path.isfile(source):
            raise CmpProcessError(
                "CMP image conversion source does not exist: {}".format(source)
            )
    if not os.path.isfile(rvio_path):
        raise CmpProcessError("CMP RVIO executable does not exist: {}".format(rvio_path))
    output_dir = os.path.dirname(destination)
    if not output_dir or not os.path.isdir(output_dir):
        raise CmpProcessError(
            "CMP review MOV output directory does not exist: {}".format(output_dir)
        )

    work_dir = tempfile.mkdtemp(
        prefix="oct_publish_cmp_preview_",
        dir=_cmp_local_temp_root(temp_root),
    )
    try:
        for frame, source in enumerate(sources):
            extension = os.path.splitext(source)[1]
            staged = os.path.join(work_dir, "img.{:06d}{}".format(frame, extension))
            shutil.copyfile(source, staged)
        kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "check": False,
        }
        if platform.system().lower() == "windows":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = runner([rvio_path, work_dir, "-o", destination], **kwargs)
        if result.returncode != 0:
            output = (result.stderr or result.stdout or "").strip()
            raise CmpProcessError(
                "CMP RVIO conversion failed ({}): {}".format(
                    result.returncode,
                    output or "no diagnostic output",
                )
            )
        if not os.path.isfile(destination):
            raise CmpProcessError(
                "CMP RVIO reported success but no MOV was created: {}".format(
                    destination
                )
            )
        if frame_probe is not None:
            actual_duration = int(frame_probe(destination) or 0)
            if actual_duration != duration:
                raise CmpProcessError(
                    "CMP generated MOV is {} frames; ShotGrid Cut requires {}".format(
                        actual_duration,
                        duration,
                    )
                )
    except Exception:
        if os.path.isfile(destination):
            os.remove(destination)
        raise
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def create_cmp_version_dirs(process_data: dict, file_system) -> str:
    """Create a new CMP version directory and preview directory safely."""
    try:
        return create_version_dirs(process_data, file_system)
    except LgtProcessError as exc:
        raise CmpProcessError(str(exc)) from exc


def copy_or_create_cmp_preview(
    process_data: dict,
    file_system,
    movie_creator,
) -> str:
    """Copy the CMP MOV or generate it from the selected image input."""
    try:
        return copy_or_create_preview(
            process_data,
            file_system,
            movie_creator,
        )
    except LgtProcessError as exc:
        raise CmpProcessError(str(exc)) from exc


def _source_preview_value(preview_paths: list[str]):
    """Keep the observable scalar contract for one source without losing many."""
    if len(preview_paths) == 1:
        return preview_paths[0]
    return list(preview_paths)


def build_cmp_daily_version_info(process_data: dict) -> dict:
    """Build the legacy-compatible CMP Dailies version_info payload."""
    context = publish_context(process_data)
    preview_paths = [
        str(path).replace("\\", "/")
        for path in context.get("preview_paths") or []
        if str(path).strip()
    ]
    script_path = str(context.get("script_path") or "").replace("\\", "/")
    if not script_path:
        raise CmpProcessError("CMP source Nuke script path is missing")
    if not preview_paths:
        raise CmpProcessError("CMP source preview path is missing")
    tag_name = str(context.get("tag_name") or "").strip()
    if not tag_name:
        raise CmpProcessError("CMP publish tag is missing")

    data = {
        "r_daily_src": None,
        "source_nk": script_path,
        "source_exr": str(process_data.get("source_exr") or "").replace("\\", "/"),
        "thumbnail_png": str(
            process_data.get("source_thumbnail_png") or ""
        ).replace("\\", "/"),
        "source_preview": _source_preview_value(preview_paths),
        "publish_mode": str(context.get("publish_mode") or ""),
        "shot_code": str(context.get("entity_code") or ""),
        "version_tag": tag_name,
        "r_daily_dst": None,
    }
    if not data["shot_code"] or data["publish_mode"].lower() != "dailies":
        raise CmpProcessError("CMP Dailies version_info context is invalid")
    return data


def write_cmp_daily_version_info(process_data: dict, file_system) -> str:
    """Write and verify CMP Dailies version_info.json in the version folder."""
    context = publish_context(process_data)
    destination = str(context.get("v_dir_json") or "")
    preview_path = str(
        process_data.get("published_preview_path")
        or context.get("v_dir_preview")
        or ""
    )
    if not destination:
        raise CmpProcessError("CMP version_info.json path is missing")
    if not file_system.file_exists(preview_path):
        raise CmpProcessError(
            "CMP published preview must exist before writing version_info: {}".format(
                preview_path
            )
        )
    data = build_cmp_daily_version_info(process_data)
    file_system.write_json(
        destination,
        data,
        overwrite=False,
        ensure_ascii=True,
    )
    if not file_system.file_exists(destination):
        raise CmpProcessError(
            "CMP version_info.json was not created: {}".format(destination)
        )
    if file_system.read_json(destination) != data:
        raise CmpProcessError(
            "CMP version_info.json verification failed: {}".format(destination)
        )
    process_data["version_info"] = data
    process_data["published_version_info"] = destination
    return destination


def create_cmp_shotgrid_version(
    process_data: dict,
    sg,
    frame_probe,
    upload_movie: str,
    now=None,
) -> dict:
    """Create/upload/connect the CMP Dailies Version using the common contract."""
    context = publish_context(process_data)
    if str(context.get("publish_mode") or "").lower() != "dailies":
        raise CmpProcessError("CMP Dailies process received a non-Dailies context")
    version_info = str(process_data.get("published_version_info") or "")
    if not version_info or not os.path.isfile(version_info):
        raise CmpProcessError(
            "CMP version_info.json must exist before ShotGrid Version creation"
        )
    try:
        return create_shotgrid_version(
            process_data,
            sg,
            frame_probe,
            upload_movie,
            now=now,
        )
    except LgtProcessError as exc:
        raise CmpProcessError(str(exc)) from exc


def lock_cmp_version(process_data: dict, locker) -> None:
    """Lock the completed CMP version only after all prior processes succeed."""
    required = (
        process_data.get("published_preview_path"),
        process_data.get("published_version_info"),
        process_data.get("created_version"),
    )
    if not all(required):
        raise CmpProcessError(
            "CMP publish outputs are incomplete; refusing to lock the version"
        )
    try:
        lock_version(process_data, locker)
    except LgtProcessError as exc:
        raise CmpProcessError(str(exc)) from exc
