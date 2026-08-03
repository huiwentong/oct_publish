"""
Dialog: view publish log output.
"""
import html
import re

from qtpy.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
from qtpy.QtCore import Qt
from qtpy.QtGui import QTextCursor
from publish_gui.ui.theme import Color, font_mono

_LEVEL_PATTERN = re.compile(r"\[(DEBUG|INFO|SUCCESS|WARNING|ERROR|CRITICAL)\]", re.IGNORECASE)

_LEVEL_COLORS = {
    "DEBUG": Color.TEXT_MUTED,
    "INFO": Color.ACCENT,
    "SUCCESS": Color.SUCCESS,
    "WARNING": Color.WARNING,
    "ERROR": Color.DANGER,
    "CRITICAL": Color.DANGER,
}


def _colorize_line(line):
    """Return HTML for one log line, tinted by its log level."""
    match = _LEVEL_PATTERN.search(line)
    if not match:
        return html.escape(line)
    color = _LEVEL_COLORS.get(match.group(1).upper(), Color.TEXT_PRIMARY)
    prefix, tag, suffix = line[: match.start()], match.group(0), line[match.end():]
    return (
        f'<span style="color:{Color.TEXT_MUTED}">{html.escape(prefix)}</span>'
        f'<span style="color:{color}; font-weight:600;">{html.escape(tag)}</span>'
        f'<span style="color:{color}">{html.escape(suffix)}</span>'
    )


def _render_log_text(text):
    """Convert plain log text to HTML with per-level colors."""
    return "<br/>".join(_colorize_line(line) for line in text.splitlines())


class LogDialog(QDialog):
    def __init__(self, log_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Publish Log")
        self.setMinimumSize(720, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"background-color: {Color.BG_DARK};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Log Output")
        header.setStyleSheet(
            f"color: {Color.TEXT_PRIMARY};"
            f"font-size: 13pt;"
            f"font-weight: bold;"
        )
        layout.addWidget(header)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(font_mono(10))
        self._log.setHtml(_render_log_text(log_text or "No log output yet.\n"))
        self._log.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {Color.BG_LIGHT};"
            f"  color: {Color.TEXT_PRIMARY};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 8px;"
            f"  padding: 12px;"
            f"}}"
        )
        layout.addWidget(self._log)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("ghost")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def append_log(self, text):
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self._log.document().isEmpty():
            cursor.insertBlock()
        cursor.insertHtml(_render_log_text(text))
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()
