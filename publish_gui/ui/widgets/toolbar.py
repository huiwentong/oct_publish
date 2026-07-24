"""
Top toolbar with action buttons (View Log, History, etc.)
"""
from qtpy.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame, QComboBox
from qtpy.QtCore import Qt, Signal # type: ignore
from publish_gui.ui.theme import Color, font_body


class ToolBar(QWidget):
    log_requested = Signal()
    history_requested = Signal()
    settings_requested = Signal()
    publish_type_changed = Signal(str)

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

        type_label = QLabel("Publish Type:")
        type_label.setStyleSheet(
            f"color: {Color.TEXT_MUTED}; background: transparent; border: none; font-size: 9pt; padding-right: 4px;"
        )
        type_label.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(type_label)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["", "Dailies", "Submit", "Publish"])
        self._type_combo.setCurrentIndex(1)
        self._type_combo.setFixedWidth(120)
        self._type_combo.currentTextChanged.connect(self.publish_type_changed.emit)
        self._type_combo.setStyleSheet(
            f"QComboBox {{"
            f"  background-color: {Color.BG_LIGHT};"
            f"  color: {Color.TEXT_PRIMARY};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 6px;"
            f"  padding: 3px 8px 3px 8px;"
            f"  font-size: 9pt;"
            f"  min-height: 0px;"
            f"  outline: none;"
            f"}}"
            f"QComboBox:focus {{"
            f"  border-color: {Color.ACCENT};"
            f"}}"
            f"QComboBox::drop-down {{"
            f"  border: none;"
            f"  width: 20px;"
            f"  subcontrol-position: top right;"
            f"  subcontrol-origin: padding;"
            f"}}"
            f"QComboBox::down-arrow {{"
            f"  width: 0;"
            f"  height: 0;"
            f"  border-left: 4px solid transparent;"
            f"  border-right: 4px solid transparent;"
            f"  border-top: 5px solid {Color.TEXT_SECONDARY};"
            f"}}"
            f"QComboBox QAbstractItemView {{"
            f"  background-color: {Color.SURFACE};"
            f"  color: {Color.TEXT_PRIMARY};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 6px;"
            f"  padding: 4px;"
            f"  outline: none;"
            f"  selection-background-color: {Color.ACCENT_DIM};"
            f"  selection-color: #ffffff;"
            f"}}"
            f"QComboBox QAbstractItemView::item {{"
            f"  padding: 4px 10px;"
            f"  min-height: 20px;"
            f"  border-radius: 4px;"
            f"}}"
            f"QComboBox QAbstractItemView::item:hover {{"
            f"  background-color: {Color.SURFACE_HOVER};"
            f"}}"
        )
        layout.addWidget(self._type_combo)

        layout.addSpacing(8)

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

    def publish_type(self) -> str:
        return self._type_combo.currentText()
