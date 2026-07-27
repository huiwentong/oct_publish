"""Page 4 - Publish form: version info, preview management."""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QFrame, QFileDialog, QSizePolicy, QApplication,QTextEdit,
    QScrollArea,QDialog
)
import tempfile
import os
import re 
from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import Qt, Signal, QSize #type: ignore
from qtpy.QtGui import QPixmap
from publish_core.cli import PublishCli, get_user
from publish_core.database.entity import SGEntity
from publish_gui.ui.theme import Color, font_header
from publish_gui.ui.screen_grab import ScreenGrabber, screen_capture_file

PUBLISH_TYPES = ["Dailies", "Submit", "Publish"]

LISTW_STYLE = f'''
QListWidget {{
    background-color: {Color.BG_LIGHT};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
}}
QWidget  {{
    background-color: {Color.BG_LIGHT};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
}}

QListWidget::item {{
    padding: 4px 8px;
}}

QListWidget::item:selected {{
    background-color: {Color.ACCENT_DIM};
}}

QListWidget::item:focus {{
    outline: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {Color.BORDER};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Color.TEXT_MUTED};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {Color.BORDER};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {Color.TEXT_MUTED};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    height: 0;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: transparent;
}}
'''


class ThumbLabel(QLabel):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(130, 70)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "QLabel { background-color: " + Color.BG_LIGHT + "; border: 1px solid " + Color.BORDER
            + "; border-radius: 6px; color: " + Color.TEXT_MUTED + "; font-size: 8pt; }")
        self.setText("No preview")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()



    def _safe_get_dialog(self):
        """
        Get the widgets dialog parent.

        just call self.window() but this is unstable in Nuke
        Previously this would
        causing a crash on exit - suspect that it's caching
        something internally which then doesn't get cleaned
        up properly...
        """
        current_widget = self
        while current_widget:
            if isinstance(current_widget, QDialog):
                return current_widget

            current_widget = current_widget.parentWidget()

        return None

    def get_screen_shot(self):
        win = self._safe_get_dialog()
        win_geom = None
        if win:
            win_geom = win.geometry()
            win.setGeometry(1000000, 1000000, win_geom.width(), win_geom.height())
            QtCore.QCoreApplication.processEvents()
            QtCore.QCoreApplication.sendPostedEvents(None, 0)
            try:
                QtCore.QCoreApplication.flush()
            except Exception:
                pass
        try:
            path, pm = screen_capture_file()
        finally:
            # restore the window:
            if win and win_geom:
                win.setGeometry(win_geom)
                QtCore.QCoreApplication.processEvents()

        return path.replace("\\", "/").split("/")[-1], path, pm




class PreviewItem(QFrame):
    remove_clicked = Signal(int)

    def __init__(self, index, name, thumb=None, parent=None):
        super().__init__(parent)
        self._index = index
        # self.setFixedHeight(30)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(
            "PreviewItem {"
            "  background: transparent;"
            "  border-bottom: 1px solid " + Color.BORDER + ";"
            "}"
        )
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        thumb_label = QLabel()
        thumb_label.setFixedSize(32, 32)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if thumb and not thumb.isNull():
            scaled = thumb.scaled(30,30,
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
            "QPushButton { background: transparent; color: " + Color.DANGER_DIM
            + "; border: none; font-size: 10pt; }"
            "QPushButton:hover { color: " + Color.DANGER + "; }"
        )
        remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self._index))
        layout.addWidget(remove_btn)

    def set_index(self, idx):
        self._index = idx


# Screenshot now captures full desktop directly (no overlay).
# Use external tools (Win+Shift+S) for region selection.

class PublishFormPage(QWidget):
    proceed_to_check = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._preview_items = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll area for main content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                             "QScrollBar:vertical { width: 8px; }")
        scroll_content = QWidget()
        scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        sc = QVBoxLayout(scroll_content)
        sc.setContentsMargins(24, 16, 24, 16)
        sc.setSpacing(12)

        # Header
        header = QLabel("Publish Settings")
        header.setFont(font_header(18))
        sc.addWidget(header)

        # ── Version Info ──
        info_group = QGroupBox("Version Info")
        self._style_group(info_group)
        vinfo = QVBoxLayout(info_group)
        vinfo.setContentsMargins(12, 20, 12, 10)
        vinfo.setSpacing(10)

        # Version row
        ver_row = QHBoxLayout()
        ver_row.setSpacing(8)
        ver_label = QLabel("Version Name:")
        ver_label.setFixedWidth(100)
        ver_row.addWidget(ver_label)
        ver_row.addSpacing(40)
        self._version_name_label = QLabel()
        self._version_name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._version_name_label.setStyleSheet("color: " + Color.TEXT_SECONDARY + "; background: transparent;")
        ver_row.addWidget(self._version_name_label, stretch=1)
        self._version_edit = QLineEdit()
        self._version_edit.editingFinished.connect(self.check_version_edit)
        self._version_edit.setPlaceholderText("e.g. v003")
        self._version_edit.setFixedSize(135, 35)
        ver_row.addWidget(self._version_edit)
        vinfo.addLayout(ver_row)

        # Tag row
        tag_row = QHBoxLayout()
        tag_row.setSpacing(8)
        tag_label = QLabel("Publish Tag:")
        tag_label.setFixedWidth(100)
        tag_row.addWidget(tag_label)
        tag_row.addSpacing(40)
        tag_row.addStretch()
        self._tag_combo = QComboBox()
        # self._tag_combo.setEditable(True)
        self._tag_combo.setPlaceholderText("Select or type tag...")
        self._tag_combo.addItems(["", "Final", "WIP", "Review", "Client"])
        self._tag_combo.setFixedWidth(135)
        tag_row.addWidget(self._tag_combo)
        vinfo.addLayout(tag_row)
        sc.addWidget(info_group)


                # ── Comment row ──
        comment_row = QHBoxLayout()
        comment_row.setSpacing(8)
        comment_label = QLabel("Comment:")
        comment_label.setFixedWidth(100)
        comment_label.setAlignment(Qt.AlignmentFlag.AlignTop)  # 顶部对齐，配合多行文本
        comment_row.addWidget(comment_label)
        comment_row.addSpacing(40)

        self._comment_edit = QTextEdit()
        self._comment_edit.setPlaceholderText("Enter publish comment here...")
        self._comment_edit.setFixedHeight(80)
        self._comment_edit.setStyleSheet(
            "QTextEdit { background: transparent; border: 1px solid #555; "
            "border-radius: 4px; padding: 4px; }"
        )
        comment_row.addWidget(self._comment_edit, stretch=1)
        vinfo.addLayout(comment_row)

        # ── Notify People row ──
        notify_row = QHBoxLayout()
        notify_row.setSpacing(8)
        notify_label = QLabel("Notify:")
        notify_label.setFixedWidth(100)
        notify_row.addWidget(notify_label)
        notify_row.addSpacing(40)

        # 下拉菜单：选择人员
        self._notify_combo = QComboBox()
        self._notify_combo.setFixedSize(160, 35)
        self._notify_combo.setPlaceholderText("Select person...")
        
        
        self.pp_model = QtGui.QStandardItemModel()
        self.completer = QtWidgets.QCompleter()
        self.completer.setModel(self.pp_model)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive) 
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains) 
        self.completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion) 
        self.completer.setMaxVisibleItems(10) 
        self._notify_combo.setCompleter(self.completer)
        self._notify_combo.setModel(self.pp_model)
        self._notify_combo.setEditable(True) 
        notify_row.addWidget(self._notify_combo)
        
        for k,v in {'test1': 12, 'test2': 123, 'test3':855}.items():
            item = QtGui.QStandardItem(k)
            item.setData(v, Qt.ItemDataRole.UserRole)
            self.pp_model.appendRow(item)

        self._notify_scroll = QScrollArea()
        self._notify_scroll.setFixedHeight(40)
        self._notify_scroll.setWidgetResizable(True)
        self._notify_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._notify_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._notify_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._notify_container = QWidget()
        self._notify_scroll.setStyleSheet(LISTW_STYLE)
        self._notify_layout = QHBoxLayout(self._notify_container)
        self._notify_layout.setContentsMargins(4, 2, 4, 2)
        self._notify_layout.setSpacing(6)
        self._notify_layout.addStretch() 
        self._notify_scroll.setWidget(self._notify_container)

        notify_row.addWidget(self._notify_scroll, stretch=1)
        vinfo.addLayout(notify_row)

        self._notified_people: dict[str, int] = {}
        self._notify_combo.currentIndexChanged.connect(self._add_notify_person)


        # ── Preview ──
        preview_group = QGroupBox("Preview")
        self._style_group(preview_group)
        p_layout = QHBoxLayout(preview_group)
        p_layout.setContentsMargins(12, 20, 12, 12)
        p_layout.setSpacing(12)

        # Left: thumbnail + pick button
        p_left = QVBoxLayout()
        p_left.setSpacing(6)
        self._thumb_label = ThumbLabel(self)
        self._thumb_label.clicked.connect(self._get_grab_screen)
        

        p_left.addWidget(self._thumb_label)
        self._pick_btn = QPushButton("Pick Preview Files")
        self._pick_btn.setStyleSheet("""
            QPushButton {
                color: #f0f1f4
                background-color: #5E81AC;
                border: 1px solid #4C566A;
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
                border-color: #5E81AC;
            }
            QPushButton:pressed {
                background-color: #4C566A;
                padding-top: 12px;
                padding-bottom: 8px;
            }
            QPushButton:disabled {
                background-color: #D8DEE9;
                color: #4C566A;
                border-color: #E5E9F0;
            }
        """)
        self._pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pick_btn.setObjectName("ghost")
        self._pick_btn.clicked.connect(self._on_choose_file)
        p_left.addWidget(self._pick_btn)
        p_layout.addLayout(p_left)

        # Right: file list
        self._preview_list = QListWidget()
        self._preview_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._preview_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._preview_list.setStyleSheet(LISTW_STYLE)
        self._preview_list.currentRowChanged.connect(self._on_preview_selected)
        p_layout.addWidget(self._preview_list, stretch=1)
        sc.addWidget(preview_group)

        # ── Publish Files ──
        self.files_group = QGroupBox("Publish Files")
        self._style_group(self.files_group)
        # files_layout = QVBoxLayout(files_group)
        # files_layout.setContentsMargins(12, 24, 12, 12)
        # files_placeholder = QLabel("Publish file list will appear here.")
        # files_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # files_placeholder.setStyleSheet("color: " + Color.TEXT_MUTED + "; background: transparent; font-size: 10pt;")
        # files_layout.addWidget(files_placeholder)
        # files_layout.addStretch()
        sc.addWidget(self.files_group)

        sc.addStretch()
        scroll.setWidget(scroll_content)
        outer.addWidget(scroll, stretch=1)

        # ── Bottom buttons (always visible) ──
        bottom = QHBoxLayout()
        bottom.setContentsMargins(24, 8, 24, 12)
        self._back_btn = QPushButton("Back")
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

    def _add_notify_person(self, index):
        if index == -1: 
            self._notify_combo.setCurrentIndex(-1)
            return
        name = self._notify_combo.itemData(index, Qt.ItemDataRole.DisplayRole)
        data = self._notify_combo.itemData(index, Qt.ItemDataRole.UserRole)
        print(name)
        print(id)
        print(self._notified_people.get(name))
        if self._notified_people.get(name): 
            self._notify_combo.setCurrentIndex(-1)
            return
        self._notified_people[name] = data
        btn = QPushButton(name)
        btn.setFixedHeight(26)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton {"
            "  background: #3a3a3a; color: #ddd; border: 1px solid #666;"
            "  border-radius: 12px; padding: 2px 12px;"
            "}"
            "QPushButton:hover { background: #c0392b; border-color: #e74c3c; }"
        )
        btn.setToolTip(f"Click to remove {name}")
        btn.clicked.connect(lambda checked=False, b=btn, n=name: self._remove_notify_person(b, n))
        self._notify_layout.insertWidget(self._notify_layout.count() - 1, btn)
        self._notify_combo.setCurrentIndex(-1)

    def _remove_notify_person(self, btn: QPushButton, name: str):
        if name in self._notified_people:
            self._notified_people.pop(name)
        self._notify_layout.removeWidget(btn)
        btn.deleteLater()


    def check_version_edit(self):
        text = self._version_edit.text().strip()
        if not re.fullmatch(r"v\d{3}", text):
            QtWidgets.QMessageBox.warning(
                self,
                "格式错误",
                f"版本号格式不正确：'{text}'\n\n要求格式：v + 3位数字，例如 v001、v012、v103",
            )
            self._version_edit.setFocus()
            self._version_edit.selectAll()



    def _style_group(self, group):
        bg = Color.BG_MID
        border = Color.BORDER
        accent_dim = Color.ACCENT_DIM
        text_sec = Color.TEXT_SECONDARY
        text_pri = Color.TEXT_PRIMARY
        bg_light = Color.BG_LIGHT
        bg_card = Color.BG_CARD
        group.setStyleSheet(
            "QGroupBox {"
            "  background-color: " + bg + ";"
            "  border: 1px solid " + border + ";"
            "  border-radius: 10px;"
            "  margin-top: 6px;"
            "  padding: 16px 16px 12px 16px;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  left: 14px;"
            "  padding: 0 6px;"
            "  color: " + text_sec + ";"
            "  font-size: 9pt;"
            "  font-weight: bold;"
            "}"
            "QGroupBox QLabel { background: transparent; }"
            "QGroupBox QLineEdit { background: transparent; }"
            "QGroupBox QComboBox {"
            "  background-color: " + bg_light + ";"
            "  border: 1px solid " + border + ";"
            "  border-radius: 6px;"
            "  padding: 4px 8px;"
            "  min-height: 22px;"
            "}"
            "QGroupBox QComboBox:hover {"
            "  border-color: " + accent_dim + ";"
            "}"
            "QGroupBox QComboBox::drop-down {"
            "  border: none;"
            "  width: 20px;"
            "}"
            "QGroupBox QComboBox QAbstractItemView {"
            "  background-color: " + bg_card + ";"
            "  border: 1px solid " + border + ";"
            "  border-radius: 6px;"
            "  padding: 4px;"
            "  color: " + text_pri + ";"
            "  selection-background-color: " + accent_dim + ";"
            "  selection-color: " + text_pri + ";"
            "  outline: none;"
            "}"
        )

    def _get_grab_screen(self):
        name, pth, pm = self._thumb_label.get_screen_shot()
        self._add_preview(name, pth, pm if not pm.isNull() else None)


    def _on_choose_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Preview Files", "",
            "Media Files (*.png *.jpg *.jpeg *.bmp *.tif *.mp4 *.mov *.avi)")
        for path in files:
            name = path.replace("\\", "/").split("/")[-1]
            is_video = any(path.lower().endswith(ext) for ext in (".mp4", ".mov", ".avi"))
            if is_video:
                pix = self._extract_video_thumb(path)
            else:
                pix = QPixmap(path)
            self._add_preview(name, path, pix if not pix.isNull() else None)

    def _extract_video_thumb(self, video_path):
        """Extract the second frame from a video using ffmpeg and return QPixmap."""
        import subprocess
        import tempfile
        import os
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            subprocess.run(
                ["ffmpeg", "-i", video_path, "-vf", "select=eq(n\\,1)", "-vframes", "1",
                 tmp_path, "-y"],
                capture_output=True, timeout=15)
            pix = QPixmap(tmp_path)
            return pix
        except Exception:
            return QPixmap()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _add_preview(self, name, path, thumb):
        idx = len(self._preview_items)
        self._preview_items.append({"name": name, "path": path, "pixmap": thumb})
        item = QListWidgetItem()
        widget = PreviewItem(idx, name, thumb)
        widget.remove_clicked.connect(self._remove_by_widget)
        item.setSizeHint(widget.sizeHint())
        self._preview_list.addItem(item)
        self._preview_list.setItemWidget(item, widget)
        self._preview_list.setCurrentRow(idx)
        # Show first added preview as thumbnail
        if idx == 0:
            self._show_thumbnail(thumb)

    def _show_thumbnail(self, pixmap):
        if pixmap and not pixmap.isNull():
            size = self._thumb_label.size()
            scaled = pixmap.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (scaled.width() - size.width()) // 2
            y = (scaled.height() - size.height()) // 2
            cropped = scaled.copy(
                x,
                y,
                size.width(),
                size.height()
            )
            self._thumb_label.setPixmap(cropped)
        else:
            self._thumb_label.clear()
            self._thumb_label.setText("No preview")

    def _remove_by_widget(self, idx):
        if 0 <= idx < len(self._preview_items):
            self._preview_items.pop(idx)
            self._preview_list.takeItem(idx)
            self._refresh_preview_indices()
            if len(self._preview_items) > 0:
                # Show next available
                self._preview_list.setCurrentRow(0)
            else:
                self._thumb_label.setText("No preview")
                self._thumb_label.setPixmap(QPixmap())

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
            if isinstance(widget, PreviewItem):
                widget.set_index(i)

    def _on_preview_selected(self, row):
        if row < 0 or row >= len(self._preview_items):
            self._thumb_label.setText("No preview")
            self._thumb_label.setPixmap(QPixmap())
            return
        item = self._preview_items[row]
        self._show_thumbnail(item.get("pixmap"))

    def _proceed(self, mode):
        data = {
            "mode": mode,
        }
        self.proceed_to_check.emit(data)

    def build_info_page(self, cli: PublishCli):
        if not cli.task_entity:
            raise RuntimeError(f'cli can not find task entity!!!')
        if cli.task_entity.sg_last_version:
            vername = '.'.join(cli.task_entity.sg_last_version.code.split('.')[:-1]) + '.'
            vernum = int(cli.task_entity.sg_last_version.code.split('.')[-1][1:])
        else:
            vername = f'{cli.task_entity.entity.code}.{cli.task_entity.step.short_name}.{cli.task_entity.content}.'
            vernum = 1
        self._version_name_label.setText(vername)
        self._version_edit.setText('v' + str(vernum).zfill(3))
        if not cli.interface:
            raise RuntimeError(f'cli can not find interface!!!')
        
        self.pp_model.clear()
        for pp in cli.all_active_pp:
            item = QtGui.QStandardItem(pp['name'])
            item.setData(pp, Qt.ItemDataRole.UserRole)
            self.pp_model.appendRow(item)

        self._tag_combo.clear()
        for tag_id in cli.interface.tag_list:
            tag_entity = SGEntity('Tag', tag_id)
            self._tag_combo.addItem(tag_entity.name, tag_entity)

    def collect_form_info(self, cli: PublishCli):
        find_num = re.fullmatch(r"v(\d{3})", self._version_edit.text())
        if not find_num:
            raise RuntimeError('版本号不符合格式')
        num = int(find_num.group(1))
        if not self._tag_combo.currentData(Qt.ItemDataRole.UserRole):
            QtWidgets.QMessageBox.warning(self, '警告', '缺少发布标签，无法提交!')
            return False
        if not self._preview_items:
            QtWidgets.QMessageBox.warning(self, '警告', '缺少预览图片/视频，无法提交!')
            return False
        if not self._comment_edit.toPlainText():
            QtWidgets.QMessageBox.warning(self, '警告', '缺少版本注释，无法提交!')
            return False
        
        cli.gui_init(
            publish_tag_id=self._tag_combo.currentData(Qt.ItemDataRole.UserRole)['id'],
            comment=self._comment_edit.toPlainText(),
            preview_paths = [item['path'] for item in self._preview_items],
            notify = [id for id in self._notified_people.values()],
            version_num=num
        )
        return True
        

    def set_back_callback(self, cb):
        self._back_btn.clicked.connect(cb)

    def set_version_name(self, name):
        self._version_name_label.setText(name)



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main = PublishFormPage()
    main.show()
    sys.exit(app.exec_())