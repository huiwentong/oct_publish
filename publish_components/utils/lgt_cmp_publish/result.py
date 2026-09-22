from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


RESULT_SUCCESS = "success"
RESULT_FAIL = "fail"
RESULT_SKIP = "skip"
VALID_RESULT_STATES = frozenset((RESULT_SUCCESS, RESULT_FAIL, RESULT_SKIP))


@dataclass(frozen=True)
class CheckResult:
    """
    Unified check result for LGT/CMP publish checks.

    States:
      - success: check passed
      - fail:    check failed, must show reason to user
      - skip:    check skipped (e.g. RV not installed), proceed allowed
    """
    name: str
    state: str  # 'success' | 'fail' | 'skip'
    reason: str = ""
    auto_description: Optional[str] = None

    def __post_init__(self):
        if self.state not in VALID_RESULT_STATES:
            raise ValueError("Unsupported result state: {}".format(self.state))
        if self.state == RESULT_FAIL and not self.reason:
            raise ValueError("A failed result must include a reason")

    @property
    def passed(self) -> bool:
        return self.state in (RESULT_SUCCESS, RESULT_SKIP)

    @property
    def failed(self) -> bool:
        return self.state == RESULT_FAIL

    @property
    def skipped(self) -> bool:
        return self.state == RESULT_SKIP

    @staticmethod
    def ok(name: str, description: str = "") -> "CheckResult":
        return CheckResult(
            name=name,
            state=RESULT_SUCCESS,
            reason="",
            auto_description=description or None,
        )

    @staticmethod
    def fail(name: str, reason: str) -> "CheckResult":
        return CheckResult(name=name, state=RESULT_FAIL, reason=reason)

    @staticmethod
    def skip(name: str, reason: str = "") -> "CheckResult":
        return CheckResult(name=name, state=RESULT_SKIP, reason=reason)

    def __str__(self) -> str:
        if self.state == RESULT_SUCCESS:
            return f"[OK] {self.name}"
        elif self.state == RESULT_SKIP:
            suffix = ": " + self.reason if self.reason else ""
            return f"[SKIP] {self.name}{suffix}"
        else:
            return f"[FAIL] {self.name}: {self.reason}"


def to_framework_status(result: CheckResult, logger=None) -> str:
    """Convert a common result to empty-success/non-empty-failure."""
    if result.skipped and logger is not None:
        logger.warning(str(result))
    if result.failed:
        return result.reason
    return ""


def from_framework_status(name: str, status: Optional[str]) -> CheckResult:
    """Convert an existing framework return value into a common result."""
    if status:
        return CheckResult.fail(name, str(status))
    return CheckResult.ok(name)
