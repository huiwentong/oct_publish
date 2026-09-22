from __future__ import annotations

import os
import re
from typing import Optional


def execute_in_nuke_main_thread(callback, *args, nuke_module=None):
    """Execute a Nuke API callback safely from framework worker threads."""
    if nuke_module is None:
        import nuke as nuke_module
    nuke_env = getattr(nuke_module, "env", None)
    try:
        is_gui = nuke_env.get("gui")
    except (AttributeError, TypeError):
        is_gui = getattr(nuke_module, "GUI", None)
    if is_gui is False:
        # Nuke Terminal already runs this script on its only application
        # thread.  executeInMainThreadWithResult is unavailable in -t mode.
        return callback(*args)
    runner = getattr(nuke_module, "executeInMainThreadWithResult", None)
    if runner is None:
        return callback(*args)
    return runner(callback, args=args)


def get_nuke_script_path() -> Optional[str]:
    """
    Get the current Nuke script path.

    Returns None if Nuke is not available or script is unsaved.
    """
    try:
        import nuke

        def query_path():
            return nuke.root().knob("name").value()

        path = execute_in_nuke_main_thread(query_path, nuke_module=nuke)
        if path and path.strip() and path.strip().lower() != "root":
            return path.replace("\\", "/")
        return None
    except ImportError:
        return None


def is_script_modified() -> bool:
    """
    Check if the current Nuke script has unsaved modifications.
    """
    try:
        import nuke

        def query_modified():
            return nuke.root().modified()

        return bool(execute_in_nuke_main_thread(query_modified, nuke_module=nuke))
    except ImportError:
        return False


def get_nuke_version() -> Optional[str]:
    """
    Get the Nuke version string (e.g. '14.1v8').
    """
    try:
        import nuke
        return nuke.NUKE_VERSION_STRING
    except ImportError:
        return None


def parse_shot_code(script_path: str) -> Optional[tuple[str, str]]:
    """
    Parse sequence and shot numbers from a Nuke script filename.

    e.g. 's42_023.Cm.v105.nk' -> ('42', '023')
         'W:/dsf/Shot_work/42/023/Cm/nuke/comp/s42_023.Cm.v105.nk' -> ('42', '023')

    Returns (seq, shot) tuple or None.
    """
    if not script_path:
        return None

    basename = os.path.basename(script_path.replace("\\", "/"))
    match = re.match(r"s?(\d+)_(\d+)", basename)
    if match:
        return (match.group(1), match.group(2))
    return None


def scan_read_nodes(script_path: Optional[str] = None) -> dict[str, str]:
    """
    Scan all Read nodes in the current Nuke script.

    Returns dict mapping node_name -> file_path.
    If script_path is provided, parses the .nk file directly without
    requiring a live Nuke session (limited: only reads file knobs).
    """
    if script_path is not None:
        return _scan_nodes_from_file(script_path, "Read")
    return _scan_live_file_nodes("Read")


def scan_deepread_nodes(script_path: Optional[str] = None) -> dict[str, str]:
    """
    Scan all DeepRead nodes in the current Nuke script.

    Returns dict mapping node_name -> file_path.
    """
    if script_path is not None:
        return _scan_nodes_from_file(script_path, "DeepRead")
    return _scan_live_file_nodes("DeepRead")


def scan_camera_nodes(script_path: Optional[str] = None) -> dict[str, str]:
    """
    Scan Camera2 nodes in the current Nuke script.

    Returns dict mapping node_name -> file_path.

    CMP Publish stores Camera2 dependencies in version_info.json using
    the same node-name-to-file-path shape as Read and DeepRead.
    """
    if script_path is not None:
        return _scan_nodes_from_file(script_path, "Camera2")
    return _scan_live_file_nodes("Camera2")


def _scan_live_file_nodes(node_type: str) -> dict[str, str]:
    """Read file-knob dependencies from a live Nuke session."""
    result = {}
    try:
        import nuke

        def query_nodes():
            values = {}
            for node in nuke.allNodes(node_type):
                file_knob = node.knob("file")
                if file_knob:
                    values[node.name()] = file_knob.value()
            return values

        result = execute_in_nuke_main_thread(query_nodes, nuke_module=nuke)
    except ImportError:
        pass
    return result


def _decode_nuke_value(value: str) -> str:
    """Remove the outer quoting used for scalar values in .nk files."""
    value = value.strip()
    if len(value) >= 2:
        if value[0] == '"' and value[-1] == '"':
            return value[1:-1].replace(r'\"', '"')
        if value[0] == "{" and value[-1] == "}":
            return value[1:-1]
    return value


def _scan_nodes_from_file(script_path: str, node_type: str) -> dict[str, str]:
    """
    Parse a .nk file to extract file-knob dependencies.

    This is a lightweight parser that reads the .nk text format
    without requiring a live Nuke session.
    """
    result = {}
    if not os.path.isfile(script_path):
        return result

    current_type = None
    current_name = None
    current_file = None

    try:
        with open(script_path, "r", encoding="utf-8") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                node_match = re.match(r"^([A-Za-z_]\w*)\s*\{\s*$", line)
                if node_match:
                    current_type = node_match.group(1)
                    current_name = None
                    current_file = None
                    continue

                if current_type is None:
                    continue

                if line == "}":
                    if (
                        current_type == node_type
                        and current_name
                        and current_file is not None
                    ):
                        result[current_name] = current_file
                    current_type = None
                    current_name = None
                    current_file = None
                    continue

                knob_match = re.match(r"^(name|file)\s+(.+)$", line)
                if not knob_match:
                    continue
                knob_name, knob_value = knob_match.groups()
                value = _decode_nuke_value(knob_value)
                if knob_name == "name":
                    current_name = value
                else:
                    current_file = value
    except (OSError, UnicodeError):
        return {}

    return result


def _scan_read_nodes_from_file(
    script_path: str,
    node_type: str = "Read",
) -> dict[str, str]:
    """Backward-compatible wrapper for earlier callers."""
    return _scan_nodes_from_file(script_path, node_type)


def build_version_info_dict(
    shot_code: str,
    version_tag: str,
    source_nk: str,
    source_preview: list[str],
    read_nodes: Optional[dict[str, str]] = None,
    deepread_nodes: Optional[dict[str, str]] = None,
    camera_nodes: Optional[dict[str, str]] = None,
) -> dict:
    """
    Build the version_info JSON dict for CMP publish.

    Matches the old tool's record_version_info_json.py structure.
    """
    info = {
        "shot_code": shot_code,
        "version_tag": version_tag,
        "source_nk": source_nk,
        "source_preview": source_preview,
    }

    if read_nodes is not None:
        info["Read"] = read_nodes
    if deepread_nodes is not None:
        info["DeepRead"] = deepread_nodes
    if camera_nodes is not None:
        info["Camera2"] = camera_nodes

    return info
