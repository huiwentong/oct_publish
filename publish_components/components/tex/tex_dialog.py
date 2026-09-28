import os
from publish_components.core import InterFace
from qtpy import QtWidgets, QtCore, QtGui
from publish_gui.ui.theme import Color

class MG:
    @property
    def current_scene(self):
        try:
            import pymel.core as pm
            scene = str(pm.sceneName())
        except:
            scene = ''
        return scene

STYLESHEET = f'''
QWidget {{
    background-color: {Color.BG_LIGHT};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
}}
QPushButton {{
    background-color: {Color.BG_CARD};
}}
'''

class SourceListWidget(QtWidgets.QListWidget):

    SUPPORTED_EXTENSIONS = {".spp", ".mra"}

    filesChanged = QtCore.Signal(list)

    MIME_TYPE = "application/x-source-list-item"

    def __init__(self, parent=None):
        super().__init__(parent)

        # 支持多选
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        # 支持拖入
        self.setAcceptDrops(True)

        # 支持拖动
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

        # 右键菜单
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

        self.placeholder_text = (
            "添加.spp / .mra 文件: 1.选中文件拖入  2.点击‘添加源文件’ \n"
            "移除.spp / .mra 文件: 1.选中目标拖出  2.选中文件右击 ‘移除选中项’ "
        )

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.count() > 0:
            return

        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

        painter.setPen(QtGui.QColor(130, 130, 130))

        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)

        # 计算文字块尺寸
        metrics = QtGui.QFontMetrics(font)
        lines = self.placeholder_text.split("\n")
        text_width = max(metrics.horizontalAdvance(line) for line in lines)
        line_height = metrics.height()
        text_height = (line_height * len(lines))

        # 稍微增加一点宽度，避免太贴
        text_width += 10

        # 整个文字块居中
        view_rect = self.viewport().rect()
        text_rect = QtCore.QRect(0, 0, text_width, text_height)
        text_rect.moveCenter(view_rect.center())

        # 文字块内部左对齐
        painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, self.placeholder_text)
        painter.end()

    def is_supported_file(self, file_path):
        if not file_path:
            return False

        if not os.path.isfile(file_path):
            return False

        ext = os.path.splitext(file_path)[1].lower()

        return ext in self.SUPPORTED_EXTENSIONS

    def get_files(self):
        result = []
        for index in range(self.count()):
            item = self.item(index)
            file_path = item.data(QtCore.Qt.UserRole)
            if file_path:
                result.append(file_path)

        return result

    def add_files(self, file_paths):

        current_files = {os.path.normcase(os.path.normpath(path)) for path in self.get_files()}
        changed = False
        for file_path in file_paths:
            if not file_path:
                continue
            file_path = os.path.abspath(os.path.normpath(file_path))
            if not self.is_supported_file(file_path):
                continue

            normalized_path = os.path.normcase(file_path)
            if normalized_path in current_files:
                continue
            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.UserRole, file_path)
            item.setToolTip(file_path)
            self.addItem(item)
            current_files.add(normalized_path)
            changed = True

        if changed:
            self.sort_items()
            self.refresh_item_names()
            self.filesChanged.emit(self.get_files())

    def refresh_item_names(self):
        name_count = {}

        for index in range(self.count()):
            item = self.item(index)
            file_path = item.data(QtCore.Qt.UserRole)
            if not file_path:
                continue
            file_name = os.path.basename(file_path)
            key = file_name.lower()
            name_count[key] = (name_count.get(key, 0) + 1)

        for index in range(self.count()):
            item = self.item(index)
            file_path = item.data(QtCore.Qt.UserRole)
            if not file_path:
                continue
            file_name = os.path.basename(file_path)
            key = file_name.lower()
            if name_count.get(key, 0) > 1:
                dir_path = os.path.dirname(file_path)
                display_name = "{}    [{}]".format(file_name, dir_path)
            else:
                display_name = file_name

            item.setText(display_name)
            item.setToolTip(file_path)

    def sort_items(self):
        files = self.get_files()
        files.sort(key=lambda path: (os.path.basename(path).lower(), path.lower()))
        self.clear()

        for file_path in files:
            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.UserRole, file_path)
            item.setToolTip(file_path)
            self.addItem(item)
        self.refresh_item_names()

    def dragEnterEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            file_paths = [
                url.toLocalFile()
                for url in mime_data.urls()
                if url.isLocalFile()
            ]

            if any(self.is_supported_file(path) for path in file_paths):
                event.acceptProposedAction()
            else:
                event.ignore()
            return

        if mime_data.hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():

            file_paths = [
                url.toLocalFile()
                for url in mime_data.urls()
                if url.isLocalFile()
            ]
            self.add_files(file_paths)

            event.acceptProposedAction()
            return

        if mime_data.hasFormat(self.MIME_TYPE):
            event.ignore()
            return
        event.ignore()

    def startDrag(self, supportedActions):
        """
        - 如果鼠标最后还在 ListWidget 内：
            不处理
        - 如果拖出 ListWidget：
            从 ListWidget 中移除
        """

        selected_items = self.selectedItems()
        if not selected_items:
            return

        selected_paths = []
        for item in selected_items:
            file_path = item.data(QtCore.Qt.UserRole)
            if file_path:
                selected_paths.append(file_path)

        if not selected_paths:
            return
        mime_data = QtCore.QMimeData()
        mime_data.setData(self.MIME_TYPE, QtCore.QByteArray(b"source-list-items"))
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec_(QtCore.Qt.MoveAction)
        global_pos = QtGui.QCursor.pos()
        local_pos = self.viewport().mapFromGlobal(global_pos)

        if self.viewport().rect().contains(local_pos):
            return
        self.remove_files(selected_paths)

    def remove_files(self, file_paths):

        normalized_paths = {os.path.normcase(os.path.normpath(path)) for path in file_paths}
        changed = False
        for index in reversed(range(self.count())):
            item = self.item(index)
            file_path = item.data(QtCore.Qt.UserRole)
            if not file_path:
                continue
            normalized_path = os.path.normcase(os.path.normpath(file_path))
            if normalized_path in normalized_paths:
                self.takeItem(index)
                changed = True

        if changed:
            self.refresh_item_names()
            self.filesChanged.emit(self.get_files())

    def on_context_menu(self, pos):
        selected_items = self.selectedItems()
        if not selected_items:
            return
        menu = QtWidgets.QMenu(self)
        remove_action = menu.addAction("移除选中项")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == remove_action:
            self.remove_selected_items()

    def remove_selected_items(self):
        selected_items = self.selectedItems()
        if not selected_items:
            return
        file_paths = []
        for item in selected_items:
            file_path = item.data(QtCore.Qt.UserRole)
            if file_path:
                file_paths.append(file_path)
        self.remove_files(file_paths)


class TexWidget(QtWidgets.QWidget):

    def __init__(self, input_form, parent=None):
        super().__init__(parent)

        self.input_form = input_form
        self.input_form.update({"ma_file": "test",
                                "src_tex_files": ["test"]
                                })
        main_layout = QtWidgets.QVBoxLayout(self)
        self.ma_widget = QtWidgets.QWidget()
        self.ma_widget.setStyleSheet(STYLESHEET)
        self.select_ma_btn = QtWidgets.QPushButton("选择MA文件")

        self.ma_line = QtWidgets.QLineEdit()
        self.ma_line.setReadOnly(True)
        self.ma_pick_btn = QtWidgets.QPushButton("<<")
        ma_layout = QtWidgets.QHBoxLayout()
        ma_layout.addWidget(self.select_ma_btn)
        ma_layout.addWidget(self.ma_line)
        ma_layout.addWidget(self.ma_pick_btn)
        self.ma_widget.setLayout(ma_layout)
        main_layout.addWidget(self.ma_widget)

        self.src_widget = QtWidgets.QWidget()
        self.src_widget.setStyleSheet(STYLESHEET)
        src_layout = QtWidgets.QVBoxLayout(self.src_widget)
        src_header_layout = QtWidgets.QHBoxLayout()
        self.src_title = QtWidgets.QLabel("收集贴图源文件")
        self.select_src_btn = QtWidgets.QPushButton("添加源文件")
        src_header_layout.addWidget(self.src_title)
        src_header_layout.addStretch()
        src_header_layout.addWidget(self.select_src_btn)
        src_layout.addLayout(src_header_layout)
        self.src_list = SourceListWidget()
        self.src_list.setMinimumHeight(150)
        src_layout.addWidget(self.src_list)
        main_layout.addWidget(self.src_widget)

        self.on_pick_current()
        self.do_connections()

    def do_connections(self):
        self.ma_pick_btn.clicked.connect(self.on_pick_current)
        self.select_ma_btn.clicked.connect(self.on_pick_workfile)
        self.select_src_btn.clicked.connect(self.on_pick_src_files)
        self.src_list.filesChanged.connect(self.on_src_files_changed)

    def on_pick_workfile(self):
        pick_dialog = QtWidgets.QFileDialog()
        pick_dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        pick_dialog.setNameFilters(["Maya File (*.ma)"])
        pick_dialog.exec_()
        l_files = pick_dialog.selectedFiles()

        if len(l_files) > 0:
            self.ma_line.setText(l_files[0])
            self.input_form.update({ "ma_file": l_files[0]})

    def on_pick_current(self):
        scene_path = MG().current_scene

        if scene_path != '':
            self.ma_line.setText(scene_path)
            self.ma_widget.setDisabled(False)
            self.input_form.update({ "ma_file": scene_path})

    def on_pick_src_files(self):
        """
        文件选择窗口支持一次选择多个 spp / mra
        """
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "选择贴图源文件",
            "",
            "Texture Source (*.spp *.mra);;"
            "Substance Painter (*.spp);;"
            "MRA File (*.mra)"
        )

        if file_paths:
            self.src_list.add_files(file_paths)

    def on_src_files_changed(self, file_paths):
        self.input_form.update({"src_tex_files": file_paths})