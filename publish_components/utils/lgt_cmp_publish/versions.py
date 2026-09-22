from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .constants import MIN_VERSION_NUMBER, MAX_VERSION_NUMBER
from .errors import VersionError


_VERSION_TOKEN_RE = re.compile(
    r"(?:^|[._-])[vV](\d{3})(?=$|[._-])"
)

_VERSION_STEP_ALIASES = {
    "lg": "lgt",
    "lgt": "lgt",
    "cm": "cmp",
    "cmp": "cmp",
}


@dataclass(frozen=True)
class FormVersionSuggestion:
    """Version prefix and editable number shown on the publish Form."""

    version_key: str
    version_num: int

    @property
    def prefix(self) -> str:
        return self.version_key + "."

    @property
    def version_text(self) -> str:
        return "v{:03d}".format(self.version_num)

    @property
    def version_name(self) -> str:
        return self.prefix + self.version_text


def parse_nuke_script_version(script_name: str) -> Optional[int]:
    """
    Parse version number from a Nuke script filename.

    Supports patterns:
      - s42_023.Cm.v105.nk   -> 105
      - s42_023_Cm_V106.nk   -> 106
      - 42_023.cmp.Cm.v106.nk -> 106
      - aaa.nk               -> None

    Returns int version number or None if not parseable.
    """
    if not script_name:
        return None

    basename = script_name.replace("\\", "/").split("/")[-1]
    matches = list(_VERSION_TOKEN_RE.finditer(basename))
    if not matches:
        return None
    return int(matches[-1].group(1))


def extract_version_from_sg_code(version_code: str) -> int:
    """
    Extract version number from a ShotGrid Version code.

    e.g. '42_023.cmp.Cm.v106' -> 106
         's42_023_Cm_V106'    -> 106

    Returns 0 if not parseable.
    """
    if not version_code:
        return 0

    matches = list(_VERSION_TOKEN_RE.finditer(version_code))
    if not matches:
        return 0
    return int(matches[-1].group(1))


def get_max_sg_version(version_codes: list[str]) -> int:
    """
    Find the maximum version number from a list of ShotGrid Version codes.
    """
    v_max = 0
    for code in version_codes:
        v_num = extract_version_from_sg_code(code)
        if v_num > v_max:
            v_max = v_num
    return v_max


def suggest_version_number(
    script_version: Optional[int],
    sg_max_version: int,
) -> int:
    """
    Calculate the suggested version number.

    Rules (matching old tool):
      1. If script_version is valid and > sg_max_version, use script_version
      2. Otherwise use sg_max_version + 1
      3. Minimum is MIN_VERSION_NUMBER (100)
      4. Maximum is MAX_VERSION_NUMBER (999)

    Raises VersionError if calculated version exceeds MAX_VERSION_NUMBER.
    """
    if script_version is not None and script_version > sg_max_version:
        suggested = script_version
    else:
        suggested = sg_max_version + 1

    if suggested < MIN_VERSION_NUMBER:
        suggested = MIN_VERSION_NUMBER

    if suggested > MAX_VERSION_NUMBER:
        raise VersionError(
            f"Version number {suggested} exceeds maximum {MAX_VERSION_NUMBER}"
        )

    return suggested


def normalize_version_step(step_short_name: str) -> str:
    """Return the MK2 token used in version names for a ShotGrid Step."""
    step_key = str(step_short_name or "").strip().lower()
    return _VERSION_STEP_ALIASES.get(step_key, step_key)


def format_version_key(
    entity_code: str,
    step_short_name: str,
    task_content: str,
) -> str:
    """Generate ``{entity}.{step}.{task}`` without a trailing dot."""
    step_token = normalize_version_step(step_short_name)
    return f"{entity_code}.{step_token}.{task_content}"


def format_version_name(
    entity_code: str,
    step_short_name: str,
    task_content: str,
    version_num: int,
) -> str:
    """
    Generate the new-style version name.

    e.g. '42_023.cmp.Cm.v106'
    """
    version_key = format_version_key(
        entity_code,
        step_short_name,
        task_content,
    )
    return f"{version_key}.v{version_num:03d}"


def build_form_version_suggestion(
    entity_code: str,
    step_short_name: str,
    task_content: str,
    script_path: Optional[str],
    sg_version_codes: Optional[list[str]] = None,
) -> FormVersionSuggestion:
    """
    Build the Form prefix and suggested number from one shared contract.

    The current workfile wins only when it is ahead of ShotGrid. Otherwise the
    next number after the highest existing Version is used, preventing a
    duplicate publish while still preserving an artist's already-versioned
    workfile.
    """
    script_version = parse_nuke_script_version(script_path or "")
    sg_max_version = get_max_sg_version(sg_version_codes or [])
    version_num = suggest_version_number(script_version, sg_max_version)
    version_key = format_version_key(
        entity_code,
        step_short_name,
        task_content,
    )
    return FormVersionSuggestion(
        version_key=version_key,
        version_num=version_num,
    )


def format_version_name_old(
    entity_code: str,
    task_content: str,
    version_num: int,
    is_asset: bool = False,
    proj_name: str = "",
) -> str:
    """
    Generate the old-style version name.

    For shots:   's42_023_Cm_V106'
    For assets:  '{proj}_{entity_code}_{task_content}_V106'
    """
    if is_asset:
        return f"{proj_name.lower()}_{entity_code}_{task_content}_V{version_num:03d}"
    else:
        return f"s{entity_code}_{task_content}_V{version_num:03d}"


def validate_version_string(version_str: str) -> bool:
    """
    Validate that a version string matches 'v' + 3 digits (e.g. 'v106').
    """
    return bool(re.fullmatch(r"v\d{3}", version_str))
