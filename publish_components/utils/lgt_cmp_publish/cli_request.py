from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .constants import DAILY_MODE, PUBLISH_MODE, SUBMIT_MODE
from .errors import PublishError


CLI_REQUEST_SCHEMA_VERSION = 1
CHECK_ONLY = "check_only"
EXECUTE = "execute"


class CliRequestError(PublishError):
    """Raised when a CLI request is incomplete, ambiguous, or unsafe."""


def _required_int(data: Mapping[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise CliRequestError("{} 必须是整数。".format(key))
    if value < minimum or value > maximum:
        raise CliRequestError(
            "{} 必须在 {} 到 {} 之间。".format(key, minimum, maximum)
        )
    return value


def _normalized_path(value: Any, label: str) -> str:
    text = str(value or "").strip().replace("\\", "/")
    if not text:
        raise CliRequestError("{} 不能为空。".format(label))
    return text


@dataclass(frozen=True)
class CliPublishRequest:
    """Versioned, GUI-independent request accepted by the LGT/CMP CLI."""

    schema_version: int
    operation: str
    task_id: int
    publish_type: str
    dcc_file: str
    version_num: int
    publish_tag_id: int
    comment: str
    preview_paths: tuple[str, ...]
    notify_user_ids: tuple[int, ...] = ()
    nuke_source_mode: str = "current"
    skip_movie_range_check: bool = False
    execute_confirm: str = ""

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        validate_files: bool = True,
    ) -> "CliPublishRequest":
        if not isinstance(data, Mapping):
            raise CliRequestError("CLI 请求根节点必须是 JSON 对象。")

        allowed_keys = {
            "schema_version",
            "operation",
            "task_id",
            "publish_type",
            "dcc_file",
            "version_num",
            "publish_tag_id",
            "comment",
            "preview_paths",
            "notify_user_ids",
            "nuke_source_mode",
            "skip_movie_range_check",
            "execute_confirm",
        }
        unknown = sorted(set(data) - allowed_keys)
        if unknown:
            raise CliRequestError(
                "CLI 请求包含未知字段：{}。".format("、".join(unknown))
            )

        schema_version = _required_int(
            data,
            "schema_version",
            CLI_REQUEST_SCHEMA_VERSION,
            CLI_REQUEST_SCHEMA_VERSION,
        )
        operation = str(data.get("operation") or CHECK_ONLY).strip().lower()
        if operation not in (CHECK_ONLY, EXECUTE):
            raise CliRequestError("operation 只能是 check_only 或 execute。")

        task_id = _required_int(data, "task_id", 1, 2147483647)
        version_num = _required_int(data, "version_num", 1, 999)
        publish_tag_id = _required_int(data, "publish_tag_id", 1, 2147483647)

        publish_type = str(data.get("publish_type") or "").strip()
        if publish_type not in (DAILY_MODE, SUBMIT_MODE, PUBLISH_MODE):
            raise CliRequestError(
                "publish_type 只能是 Dailies、Submit 或 Publish。"
            )

        dcc_file = _normalized_path(data.get("dcc_file"), "dcc_file")
        if Path(dcc_file).suffix.lower() != ".nk":
            raise CliRequestError("dcc_file 必须是 .nk 文件。")

        comment = str(data.get("comment") or "").strip()
        if len(comment) < 15:
            raise CliRequestError("comment 不能少于 15 个字符。")

        raw_previews = data.get("preview_paths")
        if not isinstance(raw_previews, (list, tuple)) or not raw_previews:
            raise CliRequestError("preview_paths 必须是非空数组。")
        preview_paths = tuple(
            _normalized_path(path, "preview_paths") for path in raw_previews
        )
        if len(set(path.lower() for path in preview_paths)) != len(preview_paths):
            raise CliRequestError("preview_paths 不能包含重复路径。")

        raw_notify = data.get("notify_user_ids") or []
        if not isinstance(raw_notify, (list, tuple)):
            raise CliRequestError("notify_user_ids 必须是整数数组。")
        notify_ids = []
        for value in raw_notify:
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise CliRequestError("notify_user_ids 必须是正整数数组。")
            if value not in notify_ids:
                notify_ids.append(value)

        nuke_source_mode = str(
            data.get("nuke_source_mode") or "current"
        ).strip().lower()
        if nuke_source_mode not in ("current", "manual"):
            raise CliRequestError(
                "nuke_source_mode 只能是 current 或 manual。"
            )

        skip_movie_range_check = data.get("skip_movie_range_check", False)
        if not isinstance(skip_movie_range_check, bool):
            raise CliRequestError("skip_movie_range_check 必须是布尔值。")

        execute_confirm = str(data.get("execute_confirm") or "").strip()
        if operation == EXECUTE and execute_confirm != "PUBLISH":
            raise CliRequestError(
                "execute 请求必须显式设置 execute_confirm 为 PUBLISH。"
            )
        if operation == CHECK_ONLY and execute_confirm:
            raise CliRequestError(
                "check_only 请求不能设置 execute_confirm。"
            )

        request = cls(
            schema_version=schema_version,
            operation=operation,
            task_id=task_id,
            publish_type=publish_type,
            dcc_file=dcc_file,
            version_num=version_num,
            publish_tag_id=publish_tag_id,
            comment=comment,
            preview_paths=preview_paths,
            notify_user_ids=tuple(notify_ids),
            nuke_source_mode=nuke_source_mode,
            skip_movie_range_check=skip_movie_range_check,
            execute_confirm=execute_confirm,
        )
        if validate_files:
            request.validate_input_files()
        return request

    @classmethod
    def from_json_file(
        cls,
        request_path: str,
        validate_files: bool = True,
    ) -> "CliPublishRequest":
        path = Path(_normalized_path(request_path, "request"))
        if not path.is_file():
            raise CliRequestError("找不到 CLI 请求文件：{}。".format(path))
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CliRequestError(
                "无法读取 CLI 请求 JSON：{}。".format(exc)
            ) from exc
        return cls.from_mapping(data, validate_files=validate_files)

    def validate_input_files(self) -> None:
        scene = Path(self.dcc_file)
        if not scene.is_file():
            raise CliRequestError("找不到 Nuke 文件：{}。".format(self.dcc_file))
        missing = [path for path in self.preview_paths if not Path(path).is_file()]
        if missing:
            raise CliRequestError(
                "找不到预览输入文件：{}。".format("、".join(missing[:5]))
            )

    def input_form(self) -> dict:
        return {
            "nk_file": self.dcc_file,
            "nuke_source_mode": self.nuke_source_mode,
            "skip_movie_range_check": self.skip_movie_range_check,
        }


def load_cli_request(
    request_path: str,
    validate_files: bool = True,
) -> CliPublishRequest:
    return CliPublishRequest.from_json_file(
        request_path,
        validate_files=validate_files,
    )
