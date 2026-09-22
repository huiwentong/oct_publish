from __future__ import annotations


def build_version_dir(publish_root: str, version_name: str) -> str:
    """
    Build the version directory path under publish_root.

    {publish_root}/{version_name}

    publish_root is resolved via old_get_path(mount_point='publish', ...).
    """
    return f"{publish_root}/{version_name}"


def build_version_dir_no_num(publish_root: str, version_key: str) -> str:
    """
    Build the no-number version directory (symlink target).

    {publish_root}/{version_key}
    """
    return f"{publish_root}/{version_key}"


def build_preview_path(version_dir: str, version_name: str) -> str:
    """Build preview MOV path: {version_dir}/preview/{version_name}.mov"""
    return f"{version_dir}/preview/{version_name}.mov"


def build_nuke_path(version_dir: str, version_name: str) -> str:
    """Build published .nk path: {version_dir}/{version_name}.nk"""
    return f"{version_dir}/{version_name}.nk"


def build_version_info_path(version_dir: str) -> str:
    """Build version_info.json path: {version_dir}/version_info.json"""
    return f"{version_dir}/version_info.json"
