"""LG/CMP-only notification ordering; never changes recipients or selection."""
from __future__ import annotations

from functools import cmp_to_key
import logging
import sys

from qtpy import QtCore


LOG = logging.getLogger(__name__)


def task_assignee_ids(task_entity):
    # Read raw links: SGEntity's property access would fetch every linked user
    # and, in the current framework, also fails for an empty entity list.
    raw = task_entity if isinstance(task_entity, dict) else task_entity.raw()
    if "task_assignees" not in raw:
        from publish_core.database.core import FastSg

        raw = FastSg().client.find_one(
            "Task", [["id", "is", raw["id"]]], ["task_assignees"],
        )
        if not raw or "task_assignees" not in raw:
            raise ValueError("Task.task_assignees is unavailable")
    return {
        link["id"] for link in (raw.get("task_assignees") or [])
        if isinstance(link, dict) and link.get("type") == "HumanUser"
        and link.get("id") is not None
    }


def pinyin_compare():
    """Return a per-call Chinese comparator without changing global locale."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        # Nuke14's QCollator(zh_CN) can fall back to Unicode order. Use the
        # Windows native Chinese collation instead; no pypinyin dependency.
        compare = ctypes.WinDLL("kernel32", use_last_error=True).CompareStringEx
        compare.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD,
            wintypes.LPCWSTR, ctypes.c_int, wintypes.LPCWSTR, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_void_p, wintypes.LPARAM,
        ]
        compare.restype = ctypes.c_int

        def compare_names(left, right):
            result = compare("zh-CN", 1, left, -1, right, -1, None, None, 0)
            if result == 0:
                raise ctypes.WinError(ctypes.get_last_error())
            return result - 2
    else:
        collator = QtCore.QCollator(QtCore.QLocale("zh_CN"))
        collator.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        compare_names = collator.compare

    # Reject silent Unicode/stroke-order fallback on unsupported Qt builds.
    if compare_names("陈", "张") >= 0 or compare_names("张", "李") <= 0:
        raise RuntimeError("Chinese pinyin collation is unavailable")
    return compare_names


def sort_notify_people(parent, task_entity):
    """Reorder existing model rows after the framework fills the common Form."""
    combo = getattr(parent, "_notify_combo", None)
    model = getattr(parent, "pp_model", None)
    if combo is None or model is None or model.rowCount() < 2:
        return False
    try:
        owners = task_assignee_ids(task_entity)
    except Exception:
        LOG.warning("通知人员：读取任务负责人失败，本次仅按姓名排序。", exc_info=True)
        owners = set()

    role = QtCore.Qt.ItemDataRole.UserRole
    indices = list(range(model.rowCount()))
    priorities = []
    names = []
    for index in indices:
        item = model.item(index, 0)
        payload = item.data(role) or {}
        priorities.append(0 if payload.get("id") in owners else 1)
        names.append(str(item.text() or "").strip())

    # Do all fallible collation before taking rows out of the live model.
    try:
        compare_names = pinyin_compare()

        def compare_rows(left, right):
            group_order = priorities[left] - priorities[right]
            if group_order:
                return group_order
            if not names[left] or not names[right]:
                return int(not names[left]) - int(not names[right])
            return compare_names(names[left], names[right])

        order = sorted(indices, key=cmp_to_key(compare_rows))
    except Exception:
        LOG.warning("通知人员：拼音排序不可用，仅置顶负责人，其余保留原顺序。", exc_info=True)
        order = sorted(indices, key=priorities.__getitem__)

    if order == indices:
        return True
    previous_index = combo.currentIndex()
    previous_blocked = combo.blockSignals(True)
    try:
        # Keep the same items, model, completion model, names and UserRole
        # dictionaries. Blocking combo signals prevents accidental recipients.
        rows = [model.takeRow(0) for _ in indices]
        for index in order:
            model.appendRow(rows[index])
        combo.setCurrentIndex(order.index(previous_index) if previous_index >= 0 else -1)
    finally:
        combo.blockSignals(previous_blocked)
    return True
