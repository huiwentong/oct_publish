from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FrameRangeError


LGT_DEFAULT_HANDLE = 50


@dataclass(frozen=True)
class FrameRange:
    """Frame range data for a shot."""
    cut_in: int
    cut_out: int
    head_in: Optional[int] = None
    tail_out: Optional[int] = None

    @property
    def cut_duration(self) -> int:
        return self.cut_out - self.cut_in + 1

    @property
    def publish_first(self) -> int:
        return self.head_in if self.head_in is not None else self.cut_in

    @property
    def publish_last(self) -> int:
        return self.tail_out if self.tail_out is not None else self.cut_out

    @property
    def publish_duration(self) -> int:
        return self.publish_last - self.publish_first + 1


def build_frame_range(
    cut_in: Optional[int],
    cut_out: Optional[int],
    head_in: Optional[int] = None,
    tail_out: Optional[int] = None,
    missing_handle_padding: Optional[int] = None,
) -> FrameRange:
    """
    Build a FrameRange from ShotGrid cut data.

    Raises FrameRangeError if cut_in/cut_out are missing or invalid.
    """
    if cut_in is None or cut_out is None:
        raise FrameRangeError("Missing cut_in or cut_out from ShotGrid")

    values = {
        "cut_in": cut_in,
        "cut_out": cut_out,
        "head_in": head_in,
        "tail_out": tail_out,
    }
    for name, value in values.items():
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise FrameRangeError("{} must be an integer".format(name))

    if cut_in > cut_out:
        raise FrameRangeError(
            f"cut_in ({cut_in}) > cut_out ({cut_out})"
        )

    if missing_handle_padding is not None:
        if (
            isinstance(missing_handle_padding, bool)
            or not isinstance(missing_handle_padding, int)
            or missing_handle_padding < 0
        ):
            raise FrameRangeError("missing_handle_padding must be a non-negative integer")
        if head_in is None:
            head_in = cut_in - missing_handle_padding
        if tail_out is None:
            tail_out = cut_out + missing_handle_padding

    publish_first = head_in if head_in is not None else cut_in
    publish_last = tail_out if tail_out is not None else cut_out
    if publish_first > cut_in or publish_last < cut_out:
        raise FrameRangeError("Head/Tail range does not contain the Cut range")

    return FrameRange(
        cut_in=cut_in,
        cut_out=cut_out,
        head_in=head_in,
        tail_out=tail_out,
    )


def frame_range_from_sg_entity(entity_data: dict) -> FrameRange:
    """
    Build FrameRange from a ShotGrid Shot entity dict.

    Expected fields: sg_ani_cut_in, sg_ani_cut_out, sg_head_in, sg_tail_out
    """
    return build_frame_range(
        cut_in=entity_data.get("sg_ani_cut_in"),
        cut_out=entity_data.get("sg_ani_cut_out"),
        head_in=entity_data.get("sg_head_in"),
        tail_out=entity_data.get("sg_tail_out"),
    )


def frame_range_for_step(entity_data: dict, step_short_name: str) -> FrameRange:
    """Build the legacy-compatible range for an LG/LGT or CMP task."""
    step = (step_short_name or "").strip().lower()
    padding = LGT_DEFAULT_HANDLE if step in ("lg", "lgt") else None
    return build_frame_range(
        cut_in=entity_data.get("sg_ani_cut_in"),
        cut_out=entity_data.get("sg_ani_cut_out"),
        head_in=entity_data.get("sg_head_in"),
        tail_out=entity_data.get("sg_tail_out"),
        missing_handle_padding=padding,
    )


def frame_count_matches_cut(frame_count: int, frame_range: FrameRange) -> bool:
    """Return whether a probed MOV/sequence count exactly matches Cut duration."""
    if isinstance(frame_count, bool) or not isinstance(frame_count, (int, float)):
        return False
    return frame_count == int(frame_count) and int(frame_count) == frame_range.cut_duration


def get_cut_duration(entity_data: dict) -> int:
    """
    Get cut duration from ShotGrid entity.

    Falls back to sg_cut_duration field if present,
    otherwise computes from cut_in/cut_out.
    """
    if entity_data.get("sg_cut_duration"):
        return entity_data["sg_cut_duration"]

    try:
        fr = frame_range_from_sg_entity(entity_data)
        return fr.cut_duration
    except FrameRangeError:
        return 0
