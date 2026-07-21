"""
Page 6 - Publish progress / result.
"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QFrame,
)
from qtpy.QtCore import Qt, QTimer, Signal # type: ignore
from publish_gui.ui.theme import Color, font_header


class PublishProgressPage(QWidget):
    done = Signal()
    STAGES = [
        "Validating inputs...",
        "Uploading files...",
        "Registering in Shotgun...",
        "Creating Version entity...",
        "Finalizing publish...",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 24, 48, 24)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_label = QLabel("\u231b")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet(f"color: {Color.ACCENT}; font-size: 48pt;")
        outer.addWidget(self._icon_label)

        self._title = QLabel("Publishing...")
        self._title.setFont(font_header(18))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(f"color: {Color.TEXT_PRIMARY};")
        outer.addWidget(self._title)
        outer.addSpacing(20)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(10)
        self._progress.setFixedWidth(400)
        outer.addWidget(self._progress, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addSpacing(12)

        self._stage_label = QLabel("")
        self._stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stage_label.setStyleSheet(f"color: {Color.TEXT_MUTED}; font-size: 10pt;")
        outer.addWidget(self._stage_label)
        outer.addStretch()

        self._result_frame = QFrame()
        self._result_frame.setVisible(False)
        self._result_frame.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {Color.BG_CARD};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 12px;"
            f"  padding: 24px;"
            f"}}"
        )
        result_layout = QVBoxLayout(self._result_frame)
        result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._result_icon = QLabel("\u2714")
        self._result_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_icon.setStyleSheet(f"color: {Color.SUCCESS}; font-size: 36pt;")
        result_layout.addWidget(self._result_icon)

        self._result_text = QLabel("Publish Successful!")
        self._result_text.setFont(font_header(16))
        self._result_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_text.setStyleSheet(f"color: {Color.TEXT_PRIMARY};")
        result_layout.addWidget(self._result_text)

        self._result_detail = QLabel("Version 3 has been published.")
        self._result_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_detail.setStyleSheet(f"color: {Color.TEXT_MUTED};")
        result_layout.addWidget(self._result_detail)

        outer.addWidget(self._result_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self._finish_btn = QPushButton("Finish")
        self._finish_btn.setObjectName("accent")
        self._finish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._finish_btn.setVisible(False)
        self._finish_btn.clicked.connect(self.done.emit)
        bottom.addWidget(self._finish_btn)
        bottom.addStretch()
        outer.addLayout(bottom)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._stage_index = 0
        self._progress_val = 0

    def start_publish(self):
        self._icon_label.setText("\u231b")
        self._icon_label.setStyleSheet(f"color: {Color.ACCENT}; font-size: 48pt;")
        self._title.setText("Publishing...")
        self._progress.setValue(0)
        self._stage_index = 0
        self._progress_val = 0
        self._result_frame.setVisible(False)
        self._finish_btn.setVisible(False)
        self._stage_label.setText(self.STAGES[0])
        self._timer.start(80)

    def _tick(self):
        self._progress_val += 1
        self._progress.setValue(min(self._progress_val, 100))
        idx = min(self._progress_val // (100 // len(self.STAGES)), len(self.STAGES) - 1)
        if idx != self._stage_index:
            self._stage_index = idx
            self._stage_label.setText(self.STAGES[idx])
        if self._progress_val >= 100:
            self._timer.stop()
            self._show_result()

    def _show_result(self):
        self._icon_label.setStyleSheet(f"color: {Color.SUCCESS}; font-size: 48pt;")
        self._icon_label.setText("\u2714")
        self._title.setText("Publish Complete")
        self._stage_label.setText("")
        self._result_frame.setVisible(True)
        self._finish_btn.setVisible(True)
