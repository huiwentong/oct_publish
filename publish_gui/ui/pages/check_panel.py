"""
Page 5 - Pre-publish validation checks panel.
"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar
)
import inspect
from publish_core.cli import PublishCli, get_user
from publish_components.core import Component
from qtpy.QtCore import Qt, QTimer, Signal, QObject, QThread # type: ignore
from qtpy.QtGui import QColor
from publish_gui.ui.theme import Color, font_header

COLOR_MAP ={
    'waiting': Color.TEXT_MUTED,
    'failed': Color.DANGER,
    'process': Color.WARNING_DIM,
    'success': Color.SUCCESS
}






MOCK_CHECKS = [

    ("File exists", "PASS", Color.SUCCESS),
    ("Naming convention", "PASS", Color.SUCCESS),
    ("Texture paths valid", "WARN", Color.WARNING),
    ("Frame range matches", "PASS", Color.SUCCESS),
    ("Cache files present", "FAIL", Color.DANGER),
    ("Version up-to-date", "PASS", Color.SUCCESS),
]



class ComponentWorker(QObject):

    finished = Signal(Component, int)
    final = Signal()
    failed = Signal(str, int)
    process = Signal(int)

    def __init__(self, comps):
        super().__init__()
        self.comps:list[Component] = comps

    def run(self):
        try:
            for row, comp in enumerate(self.comps):
                if not comp.status:
                    continue

                self.process.emit(row)
                comp.run()
                if comp.status:
                    self.failed.emit(comp.status, row)
                    break
                else:
                    self.finished.emit(comp, row)
            self.final.emit()
        except Exception as e:
            self.failed.emit(str(e), -1)
            self.final.emit()




class CheckPanelPage(QWidget):
    check_done = Signal(dict)
    go_to_publish = Signal(bool)

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

        self._table = QTableWidget(1, 3)
        self._table.itemClicked.connect(self._on_item_clicked)
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

        

        # self._table.setEnabled(False)
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
        self._publish_btn.clicked.connect(lambda: self.go_to_publish.emit(False))
        bottom.addWidget(self._publish_btn)

        outer.addLayout(bottom)

        # self._timer = QTimer(self)
        # self._timer.timeout.connect(self._tick)
        self._worker_thread = QThread()
        self._worker_thread.setObjectName('allcheck!')
        self._worker = None
        self._check_index = 0

        self._progress_val = 0
        self._checked = False
        self.auto = False

    def _run_checks(self, auto=False):
        if self._checked:
            return
        self.auto = auto
        self._run_btn.setEnabled(False)
        self._publish_btn.setEnabled(False)
        self._back_btn.setEnabled(False)
        self._progress_val = 0
        self._progress.setValue(0)
        self._status_label.setText("Running checks...")
        self._table.setEnabled(True)
        self.scan_all_check()

    def scan_all_check(self):
        all_comps = []
        for row in range(self._table.rowCount()):
            item_main = self._table.item(row, 0)
            if not item_main:
                raise RuntimeError('no status item')
            comp:Component = item_main.data(Qt.ItemDataRole.UserRole)
            all_comps.append(comp)


        self.worker = ComponentWorker(all_comps)
        self.worker.moveToThread(self._worker_thread)
        self.worker.finished.connect(self.on_component_finished)
        self.worker.process.connect(self.on_component_processing)
        self.worker.failed.connect(self.on_component_failed)
        self.worker.final.connect(self.on_all_components_finnal)
        self.worker.final.connect(self._worker_thread.quit)
        self.worker.final.connect(self.worker.deleteLater)
        self._worker_thread.started.connect(self.worker.run)
        self._worker_thread.start()



    def set_step(self, row):
        step = int(100/self._table.rowCount()) * (row+1)
        self._progress_val = step
        if self._progress_val >= 98:self._progress_val = 100
        self._progress.setValue(self._progress_val)
        if self._progress_val >= 100:
            self._checked = True
            self._status_label.setText("Checks completed.")
            self._publish_btn.setEnabled(True)
            self.check_done.emit({"status": "completed"})
            if self.auto:
                self.go_to_publish.emit(True)


    def on_all_components_finnal(self):
        self._back_btn.setEnabled(True)
        if not self._checked:
            self._run_btn.setEnabled(True)

    def on_component_finished(self, comp, row):
        item_status = self._table.item(row, 2)
        item_desc = self._table.item(row, 1)
        item_main = self._table.item(row, 0)
        if not item_status or not item_desc or not item_main:
            raise RuntimeError('can not find item_status')
        item_status.setForeground(QColor(COLOR_MAP['success']))
        item_main.setForeground(QColor(COLOR_MAP['success']))
        item_desc.setForeground(QColor(COLOR_MAP['success']))
        item_status.setText('success')
        self.set_step(row)

    
    def on_component_failed(self, msg, row):
        item_status = self._table.item(row, 2)
        item_desc = self._table.item(row, 1)
        item_main = self._table.item(row, 0)
        if not item_status or not item_desc or not item_main:
            raise RuntimeError('can not find item_status')
        item_status.setForeground(QColor(COLOR_MAP['failed']))
        item_main.setForeground(QColor(COLOR_MAP['failed']))
        item_desc.setForeground(QColor(COLOR_MAP['failed']))
        item_status.setText(msg)

    def on_component_processing(self, row):
        item_status = self._table.item(row, 2)
        item_desc = self._table.item(row, 1)
        item_main = self._table.item(row, 0)
        if not item_status or not item_desc or not item_main:
            raise RuntimeError('can not find item_status')
        item_status.setForeground(QColor(COLOR_MAP['process']))
        item_main.setForeground(QColor(COLOR_MAP['process']))
        item_desc.setForeground(QColor(COLOR_MAP['process']))
        item_status.setText('processing...')


    def set_back_callback(self, cb):
        self._back_btn.clicked.connect(cb)


    def _on_item_clicked(self, item: QTableWidgetItem):
        row = item.row()
        main_item = self._table.item(row,0)
        if not main_item:
            return
        comp = main_item.data(Qt.ItemDataRole.UserRole)
        if comp:
            comp.gui_reload()
            comp.run()





    def _fill(self, cli: PublishCli):

        self._checked = False
        self._progress.setValue(0)
        self._progress_val = 0
        self._run_btn.setEnabled(True)
        self._publish_btn.setEnabled(False)
        if not cli.interface:
            raise RuntimeWarning('can not found check files!')
        self._table.clear()

        self._table.setHorizontalHeaderLabels(["check name", "description","status"])
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setRowCount(len(cli.interface.check_files))

        cli.interface.gui_build_check()


        for row, comp in enumerate(cli.interface.check_comps):
            main_item = QTableWidgetItem(comp.name)
            main_item.setToolTip(str(comp.script_path))
            main_item.setData(Qt.ItemDataRole.UserRole, comp)
            self._table.setItem(row, 0, main_item)
            desc = inspect.getdoc(comp.gui_main)
            if not desc:
                raise RuntimeError(f'can not find {comp.name} description')
            self._table.setItem(row, 1, QTableWidgetItem(desc))
            r_item = QTableWidgetItem(comp.status)
            r_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            r_item.setForeground(QColor(COLOR_MAP['waiting']))
            self._table.setItem(row, 2, r_item)