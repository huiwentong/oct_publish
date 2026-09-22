from __future__ import annotations

from typing import Any, Optional

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTableWidgetItem

from publish_core.database.core import FastSg
from publish_gui.ui.dialogs.history_dialog import HistoryDialog

from .history import normalize_history_rows
from .shotgun import ShotGridReader


class LgtCmpHistoryDialog(HistoryDialog):
    """LG/CMP-scoped History view with deterministic, null-safe rows."""

    COLUMNS = ["Version", "Type", "Comment", "Date", "User"]

    def _populate(self, task: Any) -> None:
        reader = ShotGridReader(FastSg().client)
        project = task.project.tiny_raw()
        task_ref = task.tiny_raw()
        rows = normalize_history_rows(reader.task_versions(project, task_ref))
        self._table.setRowCount(len(rows))
        for row_index, history_row in enumerate(rows):
            for column_index, value in enumerate(history_row.display_values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row_index, column_index, item)


def install_lgt_cmp_history(ui_parent: Any, task_entity: Any) -> bool:
    """
    Replace the toolbar History callback only for an active LG/CMP interface.

    The framework dialog source remains unchanged. The callback reads the
    window's current selected Task at click time, so manual task navigation
    does not retain a stale Task reference.
    """
    if ui_parent is None:
        return False
    try:
        window = ui_parent.window()
    except (AttributeError, RuntimeError):
        return False
    toolbar = getattr(window, "_toolbar", None)
    if toolbar is None or not hasattr(toolbar, "history_requested"):
        return False
    if getattr(window, "_lgt_cmp_history_installed", False):
        return True

    original_callback = getattr(window, "_show_history", None)
    if original_callback is not None:
        try:
            toolbar.history_requested.disconnect(original_callback)
        except (RuntimeError, TypeError):
            pass

    def show_lgt_cmp_history() -> None:
        selected_task = getattr(window, "_selected_task", None) or task_entity
        dialog = LgtCmpHistoryDialog(parent=window, task=selected_task)
        dialog.exec()

    window._lgt_cmp_history_callback = show_lgt_cmp_history
    window._lgt_cmp_history_installed = True
    toolbar.history_requested.connect(show_lgt_cmp_history)
    return True
