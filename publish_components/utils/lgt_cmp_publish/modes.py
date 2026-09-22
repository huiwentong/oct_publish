from __future__ import annotations

from typing import Any

from .constants import DAILY_MODE, PUBLISH_MODE
from .errors import PublishError


class UnsupportedPublishModeError(PublishError):
    """Raised before checks or side effects for an unsupported step/mode pair."""


_STEP_ALIASES = {
    "lg": "lg",
    "lgt": "lg",
    "lighting": "lg",
    "cm": "cmp",
    "cmp": "cmp",
    "compositing": "cmp",
}

SUPPORTED_MODES = {
    "lg": (DAILY_MODE,),
    "cmp": (DAILY_MODE, PUBLISH_MODE),
}

_STEP_LABELS = {
    "lg": "LGT",
    "cmp": "CMP",
}


def _canonical_step(step_short_name: Any) -> str:
    raw = str(step_short_name or "").strip().lower()
    canonical = _STEP_ALIASES.get(raw)
    if canonical is None:
        raise UnsupportedPublishModeError(
            "无法识别发布环节：{}。已停止执行。".format(raw or "<空>")
        )
    return canonical


def validate_publish_mode(step_short_name: Any, publish_mode: Any) -> str:
    """Validate the product-supported mode matrix for both GUI and CLI."""
    step = _canonical_step(step_short_name)
    mode = str(publish_mode or "").strip()
    allowed = SUPPORTED_MODES[step]
    if mode not in allowed:
        raise UnsupportedPublishModeError(
            "{} 环节当前仅支持 {}；收到的发布模式是 {}。"
            "该模式尚未实现，已停止执行。".format(
                _STEP_LABELS[step],
                "、".join(allowed),
                mode or "<空>",
            )
        )
    return mode


def publish_mode_from_process_data(process_data: dict) -> str:
    """Read the frozen context first, with framework fields as fallbacks."""
    context = process_data.get("publish_context") or {}
    return str(
        context.get("publish_mode")
        or process_data.get("publish_type")
        or process_data.get("submit_type")
        or ""
    ).strip()


def validate_process_publish_mode(step_short_name: Any, process_data: dict) -> str:
    return validate_publish_mode(
        step_short_name,
        publish_mode_from_process_data(process_data),
    )
