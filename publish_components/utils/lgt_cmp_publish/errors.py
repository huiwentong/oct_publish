from __future__ import annotations


class PublishError(Exception):
    """Base exception for LGT/CMP publish errors."""


class VersionError(PublishError):
    """Raised when version number parsing or validation fails."""


class PathError(PublishError):
    """Raised when path generation or file system operations fail."""


class CheckError(PublishError):
    """Raised when a publish check fails with a specific reason."""


class ShotGridError(PublishError):
    """Raised when ShotGrid queries or mutations fail."""


class FrameRangeError(PublishError):
    """Raised when frame range data is missing or invalid."""
