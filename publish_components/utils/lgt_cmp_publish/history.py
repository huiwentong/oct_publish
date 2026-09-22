from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Optional

from .versions import extract_version_from_sg_code


@dataclass(frozen=True)
class HistoryRow:
    """Null-safe display data for one ShotGrid Version history row."""

    code: str
    publish_type: str
    description: str
    created_at: str
    user_name: str
    version_num: int
    created_sort_value: float

    @property
    def display_values(self) -> tuple[str, str, str, str, str]:
        return (
            self.code,
            self.publish_type,
            self.description,
            self.created_at,
            self.user_name,
        )


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _format_datetime(value: Any) -> tuple[str, float]:
    parsed = _parse_datetime(value)
    if parsed is None:
        return (str(value).strip() if value else "", 0.0)
    try:
        sort_value = parsed.timestamp()
    except (OSError, OverflowError, ValueError):
        sort_value = 0.0
    return parsed.strftime("%Y-%m-%d %H:%M:%S"), sort_value


def _user_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("login") or "")
    for field_name in ("name", "login"):
        try:
            field_value = getattr(value, field_name)
        except (AttributeError, TypeError):
            continue
        if field_value:
            return str(field_value)
    return ""


def normalize_history_row(row: dict) -> HistoryRow:
    """Convert one raw Version record to stable display and sort values."""
    code = str(row.get("code") or "")
    created_at, created_sort_value = _format_datetime(row.get("created_at"))
    return HistoryRow(
        code=code,
        publish_type=str(row.get("sg_version_type") or ""),
        description=str(row.get("description") or ""),
        created_at=created_at,
        user_name=_user_name(row.get("user")),
        version_num=extract_version_from_sg_code(code),
        created_sort_value=created_sort_value,
    )


def normalize_history_rows(rows: Iterable[dict]) -> list[HistoryRow]:
    """Return newest Version first, independent of ShotGrid return order."""
    normalized = [normalize_history_row(row) for row in rows or []]
    return sorted(
        normalized,
        key=lambda item: (item.version_num, item.created_sort_value),
        reverse=True,
    )
