from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable, Optional


PREVIEW_EMPTY = "empty"
PREVIEW_MOVIE = "movie"
PREVIEW_EXR_PNG = "exr_png_pair"
PREVIEW_SINGLE_IMAGE = "single_image"
PREVIEW_IMAGE_SEQUENCE = "image_sequence"
PREVIEW_MIXED = "mixed"

IMAGE_EXTENSIONS = frozenset(
    (".exr", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".dpx")
)


@dataclass(frozen=True)
class PreviewSelection:
    """Media classification without file-system or DCC side effects."""

    kind: str
    preview_paths: tuple[str, ...]
    pur_paths: tuple[str, ...]

    @property
    def is_empty(self) -> bool:
        return not self.preview_paths


@dataclass(frozen=True)
class SequenceAnalysis:
    """Frame-number analysis for one numbered image sequence."""

    pattern: str
    frame_numbers: tuple[int, ...]
    missing_frames: tuple[int, ...]
    unexpected_frames: tuple[int, ...]
    duplicate_frames: tuple[int, ...]
    first: int
    last: int
    padding: int

    @property
    def is_contiguous(self) -> bool:
        return not self.missing_frames and not self.duplicate_frames

    @property
    def matches_expected_range(self) -> bool:
        return self.is_contiguous and not self.unexpected_frames


def _normalize(path: str) -> str:
    return str(path).replace("\\", "/")


def _extension(path: str) -> str:
    return os.path.splitext(_normalize(path))[1].lower()


def classify_preview_paths(paths: Iterable[str]) -> PreviewSelection:
    """
    Split auxiliary .pur files and classify the remaining preview inputs.

    This deliberately does not check file existence. Component checks use the
    file-system adapter for that, keeping classification deterministic in tests.
    """
    preview_paths = []
    pur_paths = []
    for path in paths:
        normalized = _normalize(path)
        if _extension(normalized) == ".pur":
            pur_paths.append(normalized)
        else:
            preview_paths.append(normalized)

    extensions = [_extension(path) for path in preview_paths]
    if not preview_paths:
        kind = PREVIEW_EMPTY
    elif len(preview_paths) == 1 and extensions[0] == ".mov":
        kind = PREVIEW_MOVIE
    elif len(preview_paths) == 2 and set(extensions) == {".exr", ".png"}:
        kind = PREVIEW_EXR_PNG
    elif len(preview_paths) == 1 and extensions[0] in IMAGE_EXTENSIONS:
        kind = PREVIEW_SINGLE_IMAGE
    elif all(extension in IMAGE_EXTENSIONS for extension in extensions):
        kind = PREVIEW_IMAGE_SEQUENCE
    else:
        kind = PREVIEW_MIXED

    return PreviewSelection(
        kind=kind,
        preview_paths=tuple(preview_paths),
        pur_paths=tuple(pur_paths),
    )


def analyze_numbered_sequence(
    paths: Iterable[str],
    expected_first: Optional[int] = None,
    expected_last: Optional[int] = None,
) -> SequenceAnalysis:
    """
    Analyze actual numbered image files and report gaps precisely.

    All paths must share directory, prefix, numeric padding and extension.
    Expected bounds must be supplied together. The resulting pattern uses
    hashes, for example ``render/shot.####.exr``.
    """
    normalized_paths = [_normalize(path) for path in paths]
    if not normalized_paths:
        raise ValueError("No image sequence paths were supplied")
    if (expected_first is None) != (expected_last is None):
        raise ValueError("expected_first and expected_last must be supplied together")
    if expected_first is not None and expected_first > expected_last:
        raise ValueError("expected_first cannot be greater than expected_last")

    signature = None
    frames = []
    for path in normalized_paths:
        directory, _, basename = path.rpartition("/")
        match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", basename)
        if not match:
            raise ValueError("Path has no trailing frame number: {}".format(path))
        prefix, frame_token, suffix = match.groups()
        current_signature = (directory.lower(), prefix.lower(), suffix.lower(), len(frame_token))
        if signature is None:
            signature = (directory, prefix, suffix, len(frame_token))
            compare_signature = current_signature
        elif current_signature != compare_signature:
            raise ValueError("Paths do not belong to one numbered sequence")
        frames.append(int(frame_token))

    unique_frames = sorted(set(frames))
    duplicate_frames = sorted(
        frame for frame in unique_frames if frames.count(frame) > 1
    )
    if expected_first is None:
        range_first = unique_frames[0]
        range_last = unique_frames[-1]
    else:
        range_first = expected_first
        range_last = expected_last

    expected = set(range(range_first, range_last + 1))
    actual = set(unique_frames)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    directory, prefix, suffix, padding = signature
    pattern_name = prefix + ("#" * padding) + suffix
    pattern = (directory + "/" if directory else "") + pattern_name

    return SequenceAnalysis(
        pattern=pattern,
        frame_numbers=tuple(unique_frames),
        missing_frames=tuple(missing),
        unexpected_frames=tuple(unexpected),
        duplicate_frames=tuple(duplicate_frames),
        first=unique_frames[0],
        last=unique_frames[-1],
        padding=padding,
    )
