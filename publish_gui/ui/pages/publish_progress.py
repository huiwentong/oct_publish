"""
Page 6 - Publish progress / result.
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
import time 

COLOR_MAP ={
    'waiting': Color.TEXT_MUTED,
    'failed': Color.DANGER,
    'process': Color.WARNING_DIM,
    'success': Color.SUCCESS
}



class ComponentWorker(QObject):

    finished = Signal(Component, int, int)
    final = Signal()
    failed = Signal(Component, int)
    process = Signal(Component, int)

    def __init__(self, comps):
        super().__init__()
        self.comps:list[Component] = comps

    def run(self):
        try:
            for row, comp in enumerate(self.comps):
                if not comp.status:
                    continue
                self.process.emit(comp, row)
                t = time.time()
                comp.run()

                if comp.status:
                    self.failed.emit(comp, row)
                    break
                else:
                    self.finished.emit(comp, row, time.time() - t)
            self.final.emit()
        except Exception as e:
            self.failed.emit(str(e), -1)
            self.final.emit()


class PublishProgressPage(QWidget):
    done = Signal()
    all_success = Signal()
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


        self._table = QTableWidget(1, 4)
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
        outer.addWidget(self._table)
        outer.addSpacing(20)
        

        bottom = QHBoxLayout()
        bottom.addStretch()

        self._process_btn = QPushButton("Publish")
        self._process_btn.setObjectName("publish")
        self._process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._process_btn.setVisible(True)
        self._process_btn.clicked.connect(self.start_publish)

        self._finish_btn = QPushButton("Finish")
        self._finish_btn.setObjectName("accent")
        self._finish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._finish_btn.setVisible(False)
        self._finish_btn.clicked.connect(self.done.emit)
        bottom.addWidget(self._finish_btn)
        bottom.addWidget(self._process_btn)
        bottom.addStretch()
        outer.addLayout(bottom)


        self._worker_thread = QThread()
        self._worker_thread.setObjectName('allcprocess!')
        self._worker = None
        self._stage_index = 0
        self._progress_val = 0


    def start_publish(self):
        self._icon_label.setText("\u231b")
        self._icon_label.setStyleSheet(f"color: {Color.ACCENT}; font-size: 48pt;")
        self._title.setText("Publishing...")
        self._progress.setValue(0)
        self._finish_btn.setEnabled(False)
        self._process_btn.setEnabled(False)
        self._stage_index = 0
        self._progress_val = 0
        self._run_stage()


    def _show_result(self):
        self._icon_label.setStyleSheet(f"color: {Color.SUCCESS}; font-size: 48pt;")
        self._icon_label.setText("\u2714")
        self._title.setText("Publish Complete")
        self._stage_label.setText("")
        self._finish_btn.setVisible(True)
        self._finish_btn.setEnabled(True)
        self._process_btn.setVisible(False)
        self.all_success.emit()
        



    def _run_stage(self):
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
        step = int((row+1)/self._table.rowCount()) *100
        self._progress_val = step
        if self._progress_val >= 98:self._progress_val = 100
        self._progress.setValue(self._progress_val)
        if self._progress_val >= 100:
            self._show_result()


    def on_all_components_finnal(self):
        print('all finnal')
        self._process_btn.setEnabled(True)


    def on_component_finished(self, comp, row, usetime):
        comp.log.success(f'finish process {comp.name}, total use: {usetime:.2f}s')
        item_status = self._table.item(row, 3)
        item_type = self._table.item(row, 2)
        item_desc = self._table.item(row, 1)
        item_main = self._table.item(row, 0)
        if not item_status or not item_desc or not item_main:
            raise RuntimeError('can not find item_status')
        item_status.setForeground(QColor(COLOR_MAP['success']))
        item_main.setForeground(QColor(COLOR_MAP['success']))
        item_type.setForeground(QColor(COLOR_MAP['success']))
        item_desc.setForeground(QColor(COLOR_MAP['success']))
        item_status.setText('success')
        self.set_step(row)

    
    def on_component_failed(self, comp, row):
        comp.log.warning(f'process failed!: {comp.status}')
        item_status = self._table.item(row, 3)
        item_type = self._table.item(row, 2)
        item_desc = self._table.item(row, 1)
        item_main = self._table.item(row, 0)
        if not item_status or not item_desc or not item_main:
            raise RuntimeError('can not find item_status')
        item_status.setForeground(QColor(COLOR_MAP['failed']))
        item_type.setForeground(QColor(COLOR_MAP['failed']))
        item_main.setForeground(QColor(COLOR_MAP['failed']))
        item_desc.setForeground(QColor(COLOR_MAP['failed']))
        item_status.setText(comp.status)

    def on_component_processing(self, comp, row):
        comp.log.info(f'start process {comp.name}')
        item_status = self._table.item(row, 3)
        item_type = self._table.item(row, 2)
        item_desc = self._table.item(row, 1)
        item_main = self._table.item(row, 0)
        if not item_status or not item_desc or not item_main:
            raise RuntimeError('can not find item_status')
        item_status.setForeground(QColor(COLOR_MAP['process']))
        item_type.setForeground(QColor(COLOR_MAP['process']))
        item_main.setForeground(QColor(COLOR_MAP['process']))
        item_desc.setForeground(QColor(COLOR_MAP['process']))
        item_status.setText('processing...')

    def _on_item_clicked(self, item: QTableWidgetItem):
        row = item.row()
        main_item = self._table.item(row,0)
        if not main_item:
            return
        comp:Component = main_item.data(Qt.ItemDataRole.UserRole)
        if comp:
            temp_status = comp.status
            comp.gui_reload()
            comp.run()
            comp.status = temp_status





    def _fill(self, cli: PublishCli):

        self._progress.setValue(0)
        self._progress_val = 0
        self._process_btn.setEnabled(True)
        self._icon_label.setText("\u231b")
        self._title.setText('Publishing...')
        self._process_btn.setVisible(True)
        self._finish_btn.setEnabled(False)
        self._finish_btn.setVisible(False)
        if not cli.interface:
            raise RuntimeWarning('can not found check files!')
        self._table.clear()

        self._table.setHorizontalHeaderLabels(["process name", "type", "description", "status"])
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        cli.interface.gui_build_process()
        self._table.setRowCount(len(cli.interface.process_comps))
        print(cli.interface.process_comps)


        for row, comp in enumerate(cli.interface.process_comps):
            main_item = QTableWidgetItem(comp.name)
            main_item.setToolTip(str(comp.script_path))
            main_item.setData(Qt.ItemDataRole.UserRole, comp)
            self._table.setItem(row, 0, main_item)
            desc = inspect.getdoc(comp.gui_main)
            if not desc:
                print(comp.gui_main)
                print(desc)
                raise RuntimeError(f'can not find {comp.script_path} description')
            self._table.setItem(row, 1, QTableWidgetItem(comp.type))
            self._table.setItem(row, 2, QTableWidgetItem(desc))
            r_item = QTableWidgetItem(comp.status)
            r_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            r_item.setForeground(QColor(COLOR_MAP['waiting']))
            self._table.setItem(row, 3, r_item)