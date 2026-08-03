"""
Dialog: view publish log output.
"""
from qtpy.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
from qtpy.QtCore import Qt
from publish_gui.ui.theme import Color, font_mono


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
        self._log.setPlainText(log_text or "No log output yet.\n")
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
        self._log.append(text)
