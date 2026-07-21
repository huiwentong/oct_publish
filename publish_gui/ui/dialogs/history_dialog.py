"""
Dialog: view version history for a task.
"""
from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QHeaderView,
)
from qtpy.QtCore import Qt
from publish_gui.ui.theme import Color


class HistoryDialog(QDialog):
    COLUMNS = ["Version", "Status", "Comment", "Date", "User"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Version History")
        self.setMinimumSize(760, 440)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"background-color: {Color.BG_DARK};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Version History")
        header.setStyleSheet(
            f"color: {Color.TEXT_PRIMARY};"
            f"font-size: 13pt;"
            f"font-weight: bold;"
        )
        layout.addWidget(header)

        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            f"QTableWidget {{"
            f"  background-color: {Color.BG_LIGHT};"
            f"  alternate-background-color: {Color.SURFACE};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 8px;"
            f"}}"
            f"QHeaderView::section {{"
            f"  background-color: {Color.BG_MID};"
            f"  color: {Color.TEXT_SECONDARY};"
            f"  padding: 8px;"
            f"  border: none;"
            f"  border-bottom: 1px solid {Color.BORDER};"
            f"  font-weight: bold;"
            f"}}"
        )
        layout.addWidget(self._table)

        self._populate_mock()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("ghost")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _populate_mock(self):
        self._table.setRowCount(3)
        mock = [
            ("v003", "Published", "Final lighting pass", "2026-07-21", "Alice"),
            ("v002", "Published", "Address review notes", "2026-07-20", "Bob"),
            ("v001", "Draft", "Initial publish", "2026-07-19", "Alice"),
        ]
        for row, (ver, status, comment, date, user) in enumerate(mock):
            for col, val in enumerate([ver, status, comment, date, user]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)
