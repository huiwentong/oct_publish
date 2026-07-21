"""
Page 4 - Publish form built around PublishCli fields.
"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QTextEdit,
    QGroupBox, QFormLayout,
)
from qtpy.QtCore import Qt, Signal
from publish_gui.ui.theme import Color, font_header


PUBLISH_TYPES = ["Dailies", "Submit", "Publish"]


class PublishFormPage(QWidget):
    proceed_to_check = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 24, 48, 24)

        header = QLabel("Publish Settings")
        header.setFont(font_header(18))
        outer.addWidget(header)
        outer.addSpacing(16)

        body = QHBoxLayout()
        body.setSpacing(24)

        form_group = QGroupBox("Publish Info")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(20, 24, 20, 20)

        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("e.g. alice")
        self._user_edit.setText("current_user")
        form_layout.addRow("User:", self._user_edit)

        self._type_combo = QComboBox()
        self._type_combo.addItems(PUBLISH_TYPES)
        form_layout.addRow("Publish Type:", self._type_combo)

        self._version_edit = QLineEdit()
        self._version_edit.setPlaceholderText("Auto if empty")
        form_layout.addRow("Version:", self._version_edit)

        self._tag_edit = QLineEdit()
        self._tag_edit.setPlaceholderText("Optional tag ID or name")
        form_layout.addRow("Publish Tag:", self._tag_edit)

        self._dcc_edit = QLineEdit()
        self._dcc_edit.setPlaceholderText("e.g. Maya 2026")
        form_layout.addRow("DCC File:", self._dcc_edit)

        self._preview_edit = QLineEdit()
        self._preview_edit.setPlaceholderText("Path or URL to preview")
        form_layout.addRow("Preview Path:", self._preview_edit)

        self._notify_edit = QLineEdit()
        self._notify_edit.setPlaceholderText("user1, user2")
        form_layout.addRow("Notify:", self._notify_edit)

        body.addWidget(form_group, stretch=3)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)

        comment_group = QGroupBox("Comment")
        comment_layout = QVBoxLayout(comment_group)
        comment_layout.setContentsMargins(16, 20, 16, 16)
        self._comment_edit = QTextEdit()
        self._comment_edit.setPlaceholderText("Enter publish comment...")
        self._comment_edit.setMinimumHeight(100)
        self._comment_edit.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {Color.BG_LIGHT};"
            f"  color: {Color.TEXT_PRIMARY};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 8px;"
            f"  padding: 10px;"
            f"}}"
        )
        comment_layout.addWidget(self._comment_edit)
        right_panel.addWidget(comment_group)

        custom_group = QGroupBox("Custom Data")
        custom_layout = QVBoxLayout(custom_group)
        custom_layout.setContentsMargins(16, 20, 16, 16)
        custom_label = QLabel("Extra key-value pairs will appear here.")
        custom_label.setStyleSheet(f"color: {Color.TEXT_MUTED}; font-size: 9pt;")
        custom_layout.addWidget(custom_label)
        right_panel.addWidget(custom_group)

        body.addLayout(right_panel, stretch=2)
        outer.addLayout(body)
        outer.addSpacing(16)

        bottom = QHBoxLayout()
        self._back_btn = QPushButton("<- Back")
        self._back_btn.setObjectName("ghost")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom.addWidget(self._back_btn)
        bottom.addStretch()

        self._check_only_btn = QPushButton("Check Only")
        self._check_only_btn.setObjectName("ghost")
        self._check_only_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._check_only_btn.clicked.connect(lambda: self._proceed(mode="check"))
        bottom.addWidget(self._check_only_btn)

        self._check_publish_btn = QPushButton("Check & Publish")
        self._check_publish_btn.setObjectName("accent")
        self._check_publish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._check_publish_btn.clicked.connect(lambda: self._proceed(mode="both"))
        bottom.addWidget(self._check_publish_btn)

        outer.addLayout(bottom)
        self._go_back = Signal()

    def _proceed(self, mode):
        data = {
            "user": self._user_edit.text(),
            "publish_type": self._type_combo.currentText(),
            "version": self._version_edit.text(),
            "tag": self._tag_edit.text(),
            "dcc": self._dcc_edit.text(),
            "preview": self._preview_edit.text(),
            "notify": self._notify_edit.text(),
            "comment": self._comment_edit.toPlainText(),
            "mode": mode,
        }
        self.proceed_to_check.emit(data)

    def set_back_callback(self, cb):
        self._go_back.connect(cb)
        self._back_btn.clicked.connect(cb)
