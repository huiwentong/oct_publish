from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

from .errors import PathError


class FileSystemAdapter:
    """File-system boundary used by LG/CMP checks and processes."""

    def ensure_dir(self, path: str) -> str:
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            raise PathError(f"Failed to create directory {path}: {e}") from e

    def file_exists(self, path: str) -> bool:
        return os.path.isfile(path)

    def dir_exists(self, path: str) -> bool:
        return os.path.isdir(path)

    def copy_file(self, src: str, dst: str, overwrite: bool = False) -> str:
        """Copy one file, rejecting an existing destination by default."""
        try:
            if not self.file_exists(src):
                raise PathError(f"Source file not found: {src}")
            if self.file_exists(dst) and not overwrite:
                raise PathError(f"Destination file already exists: {dst}")
            dst_dir = os.path.dirname(dst)
            if dst_dir:
                self.ensure_dir(dst_dir)
            shutil.copyfile(src, dst)
            return dst
        except PathError:
            raise
        except Exception as e:
            raise PathError(f"Failed to copy {src} -> {dst}: {e}") from e

    def lock_file(self, path: str) -> None:
        try:
            if not self.file_exists(path):
                raise PathError(f"Cannot lock non-existent file: {path}")
            os.chmod(path, os.stat(path).st_mode & ~stat.S_IWRITE)
        except PathError:
            raise
        except Exception as e:
            raise PathError(f"Failed to lock {path}: {e}") from e

    def is_locked(self, path: str) -> bool:
        if not self.file_exists(path):
            return False
        return not bool(os.stat(path).st_mode & stat.S_IWRITE)

    def write_json(
        self,
        path: str,
        data: dict,
        overwrite: bool = False,
        ensure_ascii: bool = True,
    ) -> str:
        """Atomically write JSON, rejecting an existing target by default."""
        temp_path = None
        try:
            if self.file_exists(path) and not overwrite:
                raise PathError(f"Destination file already exists: {path}")
            dst_dir = os.path.dirname(path)
            if dst_dir:
                self.ensure_dir(dst_dir)
            fd, temp_path = tempfile.mkstemp(
                prefix=".oct_publish_",
                suffix=".tmp",
                dir=dst_dir or None,
            )
            os.close(fd)
            with open(temp_path, "w", encoding="utf-8") as stream:
                json.dump(data, stream, indent=4, ensure_ascii=ensure_ascii)
            os.replace(temp_path, path)
            temp_path = None
            return path
        except PathError:
            raise
        except Exception as e:
            raise PathError(f"Failed to write JSON {path}: {e}") from e
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def read_json(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as stream:
                data = json.load(stream)
            if not isinstance(data, dict):
                raise PathError(f"JSON root must be an object: {path}")
            return data
        except PathError:
            raise
        except Exception as e:
            raise PathError(f"Failed to read JSON {path}: {e}") from e


DEFAULT_FILE_SYSTEM = FileSystemAdapter()


def ensure_dir(path: str) -> str:
    return DEFAULT_FILE_SYSTEM.ensure_dir(path)


def copy_file(src: str, dst: str, overwrite: bool = False) -> str:
    return DEFAULT_FILE_SYSTEM.copy_file(src, dst, overwrite=overwrite)


def file_exists(path: str) -> bool:
    return DEFAULT_FILE_SYSTEM.file_exists(path)


def dir_exists(path: str) -> bool:
    return DEFAULT_FILE_SYSTEM.dir_exists(path)


def lock_file(path: str) -> None:
    DEFAULT_FILE_SYSTEM.lock_file(path)


def is_locked(path: str) -> bool:
    return DEFAULT_FILE_SYSTEM.is_locked(path)


def write_json(
    path: str,
    data: dict,
    overwrite: bool = False,
    ensure_ascii: bool = True,
) -> str:
    return DEFAULT_FILE_SYSTEM.write_json(
        path,
        data,
        overwrite=overwrite,
        ensure_ascii=ensure_ascii,
    )


def read_json(path: str) -> dict:
    return DEFAULT_FILE_SYSTEM.read_json(path)


def normalize_path(path: str) -> str:
    return str(path).replace("\\", "/")


def get_basename(path: str) -> str:
    return os.path.basename(normalize_path(path))


def get_dirname(path: str) -> str:
    return os.path.dirname(normalize_path(path))
