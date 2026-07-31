"""
Dialog: view version history for a task.
"""
from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QHeaderView,
)
from publish_core.database.entity import SGEntity, get_history_version
from qtpy.QtCore import Qt
from publish_gui.ui.theme import Color
from datetime import datetime


class HistoryDialog(QDialog):
    COLUMNS = ["Version", "Status", "Comment", "Date", "User"]

    def __init__(self, parent=None, task:SGEntity|None=None):
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

        if task:
            self._populate(task)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("ghost")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _populate(self, task):
        mock = get_history_version(task)
        self._table.setRowCount(len(mock))
        for row, v_dict in enumerate(mock):
            # print(created_at)
            # dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            code = v_dict['code']
            sg_version_type = v_dict['sg_version_type']
            description = v_dict['description']
            created_at = v_dict['created_at']
            user = v_dict['user']

            for col, val in enumerate([code, sg_version_type, description, created_at.strftime("%Y-%m-%d %H:%M:%S"), user['name']]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)
