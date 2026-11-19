import traceback
from dataclasses import dataclass, field

from qtpy import QtCore, QtGui, QtWidgets
from publish_components.core import InterFace
from publish_gui.ui.theme import Color
from publish_components.utils.edit_utils import parse_edl
import re
from pprint import pprint






class EditWidget(QtWidgets.QWidget):

    COLUMNS = [
        ("order",   False, "order"),
        ("name",    True,  "clip_name"),
        ("持续时长", False, "duration"),
        ("剪辑入点", False, "rec_in"),
        ("剪辑出点", False, "rec_out"),
    ]

    def __init__(self, input_form: dict, process_data:dict, isdaily: bool = False):
        super().__init__()
        self.setObjectName('EditWidget')
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        # ---- 保证 input_form 具备所需键 ----
        self.input_form = input_form
        self.isdaily = isdaily
        if not self.isdaily:
            self.input_form.setdefault("clip_data", "")
            self.input_form.setdefault("mov_file", "")
            self.input_form.setdefault("edl_file", "")
        # self.process_data = process_data

        # ---- 文件选择区 ----
        self.video_edit, self.video_btn = self._make_file_row(
            "串场视频(.mov)", "",
            "选择串场视频", "视频文件 (*.mov *.mp4 *.mxf);;所有文件 (*)",
            self._on_video_selected,
        )
        self.edl_edit, self.edl_btn = self._make_file_row(
            "EDL 文件", "",
            "选择 EDL 文件", "EDL 文件 (*.edl);;所有文件 (*)",
            self._on_edl_selected,
        )

        # ---- 表格区 ----
        self.table = QtWidgets.QTableWidget(0, len(self.COLUMNS), self)
        self.table.setHorizontalHeaderLabels([c[0] for c in self.COLUMNS])
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet("""
/* ========== 表格整体 ========== */
QTableWidget {
    background-color: #1e1e1e;
    alternate-background-color: #252526;
    color: #d4d4d4;
    gridline-color: #3c3c3c;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    selection-background-color: #094771;
    selection-color: #ffffff;
    outline: none;
    font-size: 13px;
}

/* ========== 左上角交叉区 ========== */
QTableWidget QTableCornerButton::section {
    background-color: #2d2d30;
    border: none;
    border-bottom: 1px solid #3c3c3c;
    border-right: 1px solid #3c3c3c;
}

/* ========== 表头 ========== */
QHeaderView {
    background-color: #2d2d30;
    border: none;
}

QHeaderView::section {
    background-color: #2d2d30;
    color: #cccccc;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #3c3c3c;
    border-bottom: 2px solid #007acc;
    font-weight: 600;
    font-size: 13px;
}

QHeaderView::section:hover {
    background-color: #3a3a3d;
    color: #ffffff;
}

QHeaderView::section:first {
    border-top-left-radius: 6px;
}

QHeaderView::section:last {
    border-top-right-radius: 6px;
    border-right: none;
}

/* ========== 单元格 ========== */
QTableWidget::item {
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #2a2a2a;
}

QTableWidget::item:hover {
    background-color: #2a2d2e;
}

QTableWidget::item:selected {
    background-color: #094771;
    color: #ffffff;
}

/* ========== 单元格内编辑器（双击 name 列时） ========== */
QTableWidget QLineEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #007acc;
    border-radius: 3px;
    padding: 4px 6px;
    selection-background-color: #094771;
    selection-color: #ffffff;
}

/* ========== 竖向滚动条 ========== */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #555555;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

/* ========== 横向滚动条 ========== */
QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    margin: 0;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #424242;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #555555;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}
""")
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)  
        header.setHighlightSections(False)  
        header.setDefaultAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)   
        self.table.setShowGrid(False)        
        self.table.setAlternatingRowColors(True)   
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.DoubleClicked |
            QtWidgets.QAbstractItemView.EditKeyPressed)
        self.table.itemChanged.connect(self._on_item_changed)

        # ---- 整体布局 ----
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._wrap_row(self.video_edit, self.video_btn))
        lay.addWidget(self._wrap_row(self.edl_edit, self.edl_btn))
        lay.addWidget(self.table, 1)

        # 如果 input_form 里已经有 clips，直接填表
        # if self.process_data.get("clips"):
        #     self._populate_table(self.process_data["clips"])

    # ------------------------------------------------------------------
    # 构建辅助
    # ------------------------------------------------------------------
    def _make_file_row(self, label_text, default_text, dialog_title,
                       file_filter, on_click):
        """返回 (QLineEdit, QPushButton)，供 _wrap_row 组合。"""
        edit = QtWidgets.QLineEdit(default_text, self)
        edit.setObjectName('Edit')
        edit.setReadOnly(True)
        edit.setPlaceholderText(f"请选择{label_text}")

        btn = QtWidgets.QPushButton(f"选择{label_text}", self)
        btn.clicked.connect(on_click)
        return edit, btn

    def _wrap_row(self, edit: QtWidgets.QLineEdit,
                  btn: QtWidgets.QPushButton) -> QtWidgets.QWidget:
        """把 label + edit + button 放进一行。"""
        row = QtWidgets.QWidget(self)
        lay = QtWidgets.QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel(edit.placeholderText(), row)
        lay.addWidget(label)
        lay.addWidget(edit, 1)
        lay.addWidget(btn)
        return row

    # ------------------------------------------------------------------
    # 文件选择回调
    # ------------------------------------------------------------------
    def _on_video_selected(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择串场视频", "",
            "视频文件 (*.mov *.mp4 *.mxf);;所有文件 (*)")
        if not path:
            return
        self.input_form["mov_file"] = path
        self.video_edit.setText(path)

    def _on_edl_selected(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择 EDL 文件", "",
            "EDL 文件 (*.edl);;所有文件 (*)")
        if not path:
            return
        self.input_form["edl_file"] = path
        self.edl_edit.setText(path)

        try:
            clips = parse_edl(path, fps=self.input_form.get("fps", 24))
            self.input_form['clip_data'] = clips
        except Exception as e:  
            QtWidgets.QMessageBox.critical(self, "解析 EDL 失败", str(e))
            return
        self._populate_table(clips)

    # ------------------------------------------------------------------
    # 表格相关
    # ------------------------------------------------------------------
    def _populate_table(self, clips):
        """根据 clips 重填表格。"""
        self.table.blockSignals(True)          # 批量填充时屏蔽 itemChanged
        self.table.setRowCount(0)
        self.table.setRowCount(len(clips))

        for row, clip in enumerate(clips):
            for col, (_, editable, key) in enumerate(self.COLUMNS):
                value = clip.get(key, "")
                item = QtWidgets.QTableWidgetItem(str(value))
                if not editable:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.table.setItem(row, col, item)
            # 用 UserRole 记住该行对应的 clip，编辑回写时定位用
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, row)

        self.table.blockSignals(False)

    def _on_item_changed(self, item: QtWidgets.QTableWidgetItem):
        """name 列被编辑：同步回 input_form['clips']。"""
        col = item.column()
        if not self.COLUMNS[col][1]:   # 非可编辑列，忽略
            return
        row = item.row()
        key = self.COLUMNS[col][2]
        clips = self.input_form['clip_data']
        if 0 <= row < len(clips):
            clips[row][key] = item.text()





@dataclass
class CompInterface(InterFace):

    submit_form: dict = field(
        default_factory=lambda: {
            "clip_data": '-',
            "mov_file": '-',
            "edl_file": '-'
        }
    )

    tag_list: list = field(
        default_factory=lambda: [283, 282]
    )

    downstream_dcc_only: str | None = None

    def gui_pre_interface(self):
        pass

    def init_ui(self, parent: QtWidgets.QWidget):
        lay_widget = EditWidget(self.input_form, self.process_data, isdaily=self.submit_type == "Dailies")
        publish_layout = QtWidgets.QVBoxLayout(parent.files_group)
        publish_layout.setContentsMargins(0, 0, 0, 0)
        publish_layout.addWidget(lay_widget, 1)
        if self.submit_type == "Dailies":
            lay_widget.setEnabled(False)

        path = 'Z:/TD/pipeline/resource/oct_publish/edt_preview.png'
        name = path.replace("\\", "/").split("/")[-1]
        is_video = any(path.lower().endswith(ext) for ext in (".mp4", ".mov", ".avi"))
        if is_video:
            pix = parent._extract_video_thumb(path)
        else:
            pix = QtGui.QPixmap(path)
        parent._add_preview(name, path, pix if not pix.isNull() else None)

    def gui_post_interface(self):
        pass

