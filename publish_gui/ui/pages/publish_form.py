"""
Page 4 - Publish form: version info, preview management, pipeline step placeholder.
"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QFormLayout, QFrame, QFileDialog, QSizePolicy,
)
from qtpy.QtCore import Qt, Signal, QSize
from qtpy.QtGui import QPixmap
from publish_gui.ui.theme import Color, font_header


PUBLISH_TYPES = ["Dailies", "Submit", "Publish"]


class PreviewItem(QFrame):
    remove_clicked = Signal(int)

    def __init__(self, index, name, thumb=None, parent=None):
        super().__init__(parent)
        self._index = index
        self.setFixedHeight(40)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(
            "PreviewItem {"
            "  background: transparent;"
            "  border-bottom: 1px solid " + Color.BORDER + ";"
            "}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        thumb_label = QLabel()
        thumb_label.setFixedSize(32, 32)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if thumb and not thumb.isNull():
            scaled = thumb.scaled(32, 32,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            thumb_label.setPixmap(scaled)
        else:
            thumb_label.setText("[img]")
            thumb_label.setStyleSheet("color: " + Color.TEXT_MUTED + "; font-size: 9pt;")
        layout.addWidget(thumb_label)

        name_label = QLabel(name)
        name_label.setStyleSheet(
            "color: " + Color.TEXT_PRIMARY + "; background: transparent; font-size: 9pt;")
        layout.addWidget(name_label, stretch=1)

        remove_btn = QPushButton("X")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet(
            "QPushButton { background: transparent; color: " + Color.TEXT_MUTED
            + "; border: none; font-size: 10pt; }"
            "QPushButton:hover { color: " + Color.DANGER + "; }"
        )
        remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self._index))
        layout.addWidget(remove_btn)

    def set_index(self, idx):
        self._index = idx


class PublishFormPage(QWidget):
    proceed_to_check = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._preview_items = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 16, 24, 16)
        outer.setSpacing(12)

        header = QLabel("Publish Settings")
        header.setFont(font_header(18))
        outer.addWidget(header)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        info_group = QGroupBox("Basic Version Info")
        self._style_group(info_group)
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(12, 20, 12, 12)

        self._version_edit = QLineEdit()
        self._version_edit.setPlaceholderText("e.g. v003")
        info_layout.addRow("Version:", self._version_edit)
        self._type_combo = QComboBox()
        self._type_combo.addItems(PUBLISH_TYPES)
        info_layout.addRow("Publish Type:", self._type_combo)
        self._tag_combo = QComboBox()
        self._tag_combo.setEditable(True)
        self._tag_combo.setPlaceholderText("Select or type tag...")
        self._tag_combo.addItems(["", "Final", "WIP", "Review", "Client"])
        info_layout.addRow("Publish Tag:", self._tag_combo)
        top_row.addWidget(info_group, stretch=3)

        self._step_group = QGroupBox("Pipeline Step")
        self._style_group(self._step_group)
        self._step_layout = QVBoxLayout(self._step_group)
        self._step_layout.setContentsMargins(12, 20, 12, 12)
        self._step_layout.setSpacing(8)
        self._step_placeholder = QLabel("Pipeline interface will appear here.")
        self._step_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._step_placeholder.setStyleSheet(
            "color: " + Color.TEXT_MUTED + "; background: transparent; font-size: 10pt;")
        self._step_layout.addWidget(self._step_placeholder)
        self._step_layout.addStretch()
        top_row.addWidget(self._step_group, stretch=2)
        outer.addLayout(top_row)

        preview_group = QGroupBox("Preview")
        self._style_group(preview_group)
        preview_layout = QHBoxLayout(preview_group)
        preview_layout.setContentsMargins(12, 20, 12, 12)
        preview_layout.setSpacing(12)

        preview_left = QVBoxLayout()
        preview_left.setSpacing(8)
        self._preview_display = QLabel()
        self._preview_display.setMinimumSize(320, 200)
        self._preview_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_display.setStyleSheet(
            "background-color: " + Color.BG_LIGHT + ";"
            "border: 1px solid " + Color.BORDER + ";"
            "border-radius: 8px;"
            "color: " + Color.TEXT_MUTED + ";"
            "font-size: 10pt;"
        )
        self._preview_display.setText("No preview selected")
        preview_left.addWidget(self._preview_display, stretch=1)

        preview_actions = QHBoxLayout()
        preview_actions.setSpacing(8)
        screenshot_btn = QPushButton("Screenshot")
        screenshot_btn.setObjectName("ghost")
        screenshot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        screenshot_btn.clicked.connect(self._on_screenshot)
        preview_actions.addWidget(screenshot_btn)
        choose_btn = QPushButton("Choose File...")
        choose_btn.setObjectName("ghost")
        choose_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        choose_btn.clicked.connect(self._on_choose_file)
        preview_actions.addWidget(choose_btn)
        preview_actions.addStretch()
        preview_left.addLayout(preview_actions)
        preview_layout.addLayout(preview_left, stretch=3)

        preview_right = QVBoxLayout()
        preview_right.setSpacing(6)
        sidebar_header = QLabel("Selected Previews")
        sidebar_header.setStyleSheet(
            "color: " + Color.TEXT_SECONDARY + "; background: transparent;"
            "font-size: 10pt; font-weight: bold;")
        preview_right.addWidget(sidebar_header)
        self._preview_list = QListWidget()
        self._preview_list.setStyleSheet(
            "QListWidget {"
            "  background-color: " + Color.BG_LIGHT + ";"
            "  border: 1px solid " + Color.BORDER + ";"
            "  border-radius: 8px;"
            "  padding: 2px;"
            "}"
            "QListWidget::item { border: none; padding: 0; }"
            "QListWidget::item:selected {"
            "  background-color: " + Color.ACCENT_DIM + ";"
            "  border-radius: 4px;"
            "}"
        )
        self._preview_list.currentRowChanged.connect(self._on_preview_selected)
        preview_right.addWidget(self._preview_list, stretch=1)

        preview_controls = QHBoxLayout()
        preview_controls.setSpacing(4)
        up_btn = QPushButton("Up")
        up_btn.setFixedHeight(28)
        up_btn.setObjectName("ghost")
        up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        up_btn.clicked.connect(lambda: self._move_preview(-1))
        preview_controls.addWidget(up_btn)
        down_btn = QPushButton("Down")
        down_btn.setFixedHeight(28)
        down_btn.setObjectName("ghost")
        down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        down_btn.clicked.connect(lambda: self._move_preview(1))
        preview_controls.addWidget(down_btn)
        del_btn = QPushButton("Delete")
        del_btn.setObjectName("danger")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(self._delete_preview)
        preview_controls.addWidget(del_btn)
        preview_controls.addStretch()
        preview_right.addLayout(preview_controls)
        preview_layout.addLayout(preview_right, stretch=2)
        outer.addWidget(preview_group, stretch=1)

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
        self._check_publish_btn = QPushButton("Check and Publish")
        self._check_publish_btn.setObjectName("accent")
        self._check_publish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._check_publish_btn.clicked.connect(lambda: self._proceed(mode="both"))
        bottom.addWidget(self._check_publish_btn)
        outer.addLayout(bottom)
        self._go_back = Signal()
        self._build_interface()

    def _style_group(self, group):
        group.setStyleSheet(
            "QGroupBox {"
            "  background-color: " + Color.BG_MID + ";"
            "  border: 1px solid " + Color.BORDER + ";"
            "  border-radius: 10px;"
            "  margin-top: 20px;"
            "  padding: 20px 16px 16px 16px;"
            "  font-weight: bold;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  padding: 4px 12px;"
            "  color: " + Color.TEXT_SECONDARY + ";"
            "}"
        )

    def _on_choose_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Preview Files", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif);;Videos (*.mp4 *.mov *.avi)")
        for path in files:
            name = path.replace("\\", "/").split("/")[-1]
            pix = QPixmap(path)
            self._add_preview(name, path, pix if not pix.isNull() else None)

    def _on_screenshot(self):
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"screenshot_{ts}.png"
        self._add_preview(name, name, None)

    def _add_preview(self, name, path, thumb):
        idx = len(self._preview_items)
        self._preview_items.append({"name": name, "path": path, "pixmap": thumb})
        item = QListWidgetItem()
        widget = PreviewItem(idx, name, thumb)
        widget.remove_clicked.connect(self._remove_by_widget)
        item.setSizeHint(QSize(0, 40))
        self._preview_list.addItem(item)
        self._preview_list.setItemWidget(item, widget)

    def _remove_by_widget(self, idx):
        if 0 <= idx < len(self._preview_items):
            self._preview_items.pop(idx)
            self._preview_list.takeItem(idx)
            self._refresh_preview_indices()
            self._preview_display.setText("No preview selected")

    def _delete_preview(self):
        row = self._preview_list.currentRow()
        if row >= 0:
            self._remove_by_widget(row)

    def _move_preview(self, direction):
        row = self._preview_list.currentRow()
        new_row = row + direction
        if row < 0 or new_row < 0 or new_row >= len(self._preview_items):
            return
        self._preview_items[row], self._preview_items[new_row] = (
            self._preview_items[new_row], self._preview_items[row])
        item_row = self._preview_list.takeItem(row)
        self._preview_list.insertItem(new_row, item_row)
        self._preview_list.setCurrentRow(new_row)
        self._refresh_preview_indices()

    def _refresh_preview_indices(self):
        for i in range(self._preview_list.count()):
            item = self._preview_list.item(i)
            widget = self._preview_list.itemWidget(item)
            if widget and hasattr(widget, "set_index"):
                widget.set_index(i)

    def _on_preview_selected(self, row):
        if row < 0 or row >= len(self._preview_items):
            self._preview_display.setText("No preview selected")
            return
        item = self._preview_items[row]
        pm = item.get("pixmap")
        if pm and not pm.isNull():
            scaled = pm.scaled(
                self._preview_display.width() - 4,
                self._preview_display.height() - 4,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self._preview_display.setPixmap(scaled)
        else:
            self._preview_display.setText(item["name"] + " (Preview not available)")

    def _build_interface(self):
        if hasattr(self, "_step_placeholder") and self._step_placeholder is not None:
            self._step_layout.removeWidget(self._step_placeholder)
            self._step_placeholder.deleteLater()
            self._step_placeholder = None

    def _proceed(self, mode):
        data = {
            "publish_type": self._type_combo.currentText(),
            "version": self._version_edit.text(),
            "tag": self._tag_combo.currentText(),
            "previews": [p["path"] for p in self._preview_items],
            "mode": mode,
        }
        self.proceed_to_check.emit(data)

    def set_back_callback(self, cb):
        self._back_btn.clicked.connect(cb)
