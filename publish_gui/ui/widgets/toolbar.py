"""
Top toolbar with action buttons (View Log, History, etc.)
"""
from qtpy.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
from qtpy.QtCore import Qt, Signal # type: ignore
from publish_gui.ui.theme import Color, font_body


class ToolBar(QWidget):
    log_requested = Signal()
    history_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(
            f"background-color: {Color.BG_MID};"
            f"border-bottom: 1px solid {Color.BORDER};"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)

        title = QLabel("OCT Publish Manager")
        title.setStyleSheet(
            f"color: {Color.TEXT_PRIMARY};"
            f"font-weight: bold;"
            f"font-size: 12pt;"
            f"background: transparent;"
            f"border: none;"
        )
        title.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(title)
        layout.addStretch()

        for label_text, sig in [
            ("View Log", self.log_requested),
            ("History", self.history_requested),
            ("Settings", self.settings_requested),
        ]:
            btn = QPushButton(label_text)
            btn.setObjectName("ghost")
            btn.setFont(font_body(9))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            ss = (
                f"QPushButton {{"
                f"  color: {Color.TEXT_SECONDARY};"
                f"  padding: 6px 14px;"
                f"  border: 1px solid transparent;"
                f"  border-radius: 6px;"
                f"  background: transparent;"
                f"}}"
                f"QPushButton:hover {{"
                f"  color: {Color.TEXT_PRIMARY};"
                f"  border-color: {Color.BORDER};"
                f"  background: {Color.SURFACE};"
                f"}}"
            )
            btn.setStyleSheet(ss)
            btn.clicked.connect(sig.emit)
            layout.addWidget(btn)

        self._status = QLabel("Selecting Project...")
        self._status.setStyleSheet(
            f"color: {Color.TEXT_MUTED};"
            f"padding: 4px 14px;"
            f"border: 1px solid {Color.BORDER};"
            f"border-radius: 12px;"
            f"font-size: 9pt;"
        )
        layout.addWidget(self._status)

    def set_status(self, text):
        self._status.setText(text)
