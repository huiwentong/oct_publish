"""
Page 5 - Pre-publish validation checks panel.
"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar,
)
from qtpy.QtCore import Qt, QTimer, Signal # type: ignore
from qtpy.QtGui import QColor
from publish_gui.ui.theme import Color, font_header


MOCK_CHECKS = [
    ("File exists", "PASS", Color.SUCCESS),
    ("Naming convention", "PASS", Color.SUCCESS),
    ("Texture paths valid", "WARN", Color.WARNING),
    ("Frame range matches", "PASS", Color.SUCCESS),
    ("Cache files present", "FAIL", Color.DANGER),
    ("Version up-to-date", "PASS", Color.SUCCESS),
]


class CheckPanelPage(QWidget):
    check_done = Signal(dict)
    go_to_publish = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 24, 48, 24)

        header = QLabel("Pre-Publish Checks")
        header.setFont(font_header(18))
        outer.addWidget(header)
        outer.addSpacing(16)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        self._progress.setFixedHeight(10)
        outer.addWidget(self._progress)

        self._status_label = QLabel("Waiting to start checks...")
        self._status_label.setStyleSheet(f"color: {Color.TEXT_MUTED};")
        outer.addWidget(self._status_label)
        outer.addSpacing(12)

        self._table = QTableWidget(len(MOCK_CHECKS), 2)
        self._table.setHorizontalHeaderLabels(["Check", "Result"])
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(
            f"QTableWidget {{"
            f"  background-color: {Color.BG_LIGHT};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 10px;"
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

        for row, (check, result, color) in enumerate(MOCK_CHECKS):
            self._table.setItem(row, 0, QTableWidgetItem(check))
            r_item = QTableWidgetItem(result)
            r_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            r_item.setForeground(QColor(color))
            self._table.setItem(row, 1, r_item)

        self._table.setEnabled(False)
        outer.addWidget(self._table)
        outer.addSpacing(20)

        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet(f"color: {Color.TEXT_SECONDARY};")
        outer.addWidget(self._summary_label)
        outer.addStretch()

        bottom = QHBoxLayout()
        self._back_btn = QPushButton("<- Back")
        self._back_btn.setObjectName("ghost")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom.addWidget(self._back_btn)
        bottom.addStretch()

        self._run_btn = QPushButton("Run Checks")
        self._run_btn.setObjectName("accent")
        self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_btn.clicked.connect(self._run_checks)
        bottom.addWidget(self._run_btn)

        self._publish_btn = QPushButton("Proceed to Publish ->")
        self._publish_btn.setObjectName("success")
        self._publish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._publish_btn.setEnabled(False)
        self._publish_btn.clicked.connect(lambda: self.go_to_publish.emit({}))
        bottom.addWidget(self._publish_btn)

        outer.addLayout(bottom)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._progress_val = 0
        self._checked = False

    def _run_checks(self):
        if self._checked:
            return
        self._run_btn.setEnabled(False)
        self._progress_val = 0
        self._progress.setValue(0)
        self._status_label.setText("Running checks...")
        self._table.setEnabled(True)
        self._timer.start(50)

    def _tick(self):
        self._progress_val += 2
        self._progress.setValue(self._progress_val)
        if self._progress_val >= 100:
            self._timer.stop()
            self._checked = True
            self._status_label.setText("Checks completed.")
            self._summary_label.setText("3 passed  |  1 warning  |  1 failed  |  1 pending")
            self._publish_btn.setEnabled(True)
            self.check_done.emit({"status": "completed"})

    def set_back_callback(self, cb):
        self._back_btn.clicked.connect(cb)
