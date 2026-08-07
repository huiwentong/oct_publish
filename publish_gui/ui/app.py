"""
Main publish window – orchestrates all wizard pages via QStackedWidget.
"""
import traceback

from qtpy.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QMessageBox, QDialog
)
from qtpy.QtCore import Qt, QSize, QThread, Signal, QObject #type:ignore
from qtpy.QtGui import QIcon
from publish_core.cli import PublishCli
from publish_core.log.core import PublishLog
from publish_core.cli import PublishCli, get_user
from publish_core.database.entity import SGEntity
from publish_gui.ui.theme import Color, STYLESHEET
from publish_gui.ui.widgets import StepNavBar, ToolBar, LoadingOverlay
from publish_gui.ui.dialogs import LogDialog, HistoryDialog
from publish_gui.ui.pages import (
    MyTaskSelectPage,
    ProjectSelectPage,
    EntitySelectPage,
    TaskSelectPage,
    PublishFormPage,
    CheckPanelPage,
    PublishProgressPage,
)


class PublishCliWorker(QObject):
    """Creates PublishCli in a background thread so the GUI stays responsive."""
    finished = Signal(object)  # emits PublishCli instance
    error = Signal(str)

    def __init__(self, user, task_id, publish_type, widget, log, parent=None, dcc=None):
        super().__init__(parent)
        self._user = user
        self._task_id = task_id
        self.dcc = dcc
        self._publish_type = publish_type
        self._widget = widget
        self._log = log

    def run(self):
        try:
            cli = PublishCli(
                user=self._user,
                dcc=self.dcc,
                log=self._log,
                task_id=self._task_id,
                gui=True,
                publish_type=self._publish_type,
                widget=self._widget,
            )
            if cli.task_entity:
                load = cli.task_entity.sg_last_version

            self.finished.emit(cli)
        except Exception as e:
            self._log.error(traceback.format_exc())
            self.error.emit(str(e))


class MainWindow(QDialog):
    """Root application window."""

    def __init__(self, dcc, parent=None):
        super().__init__(parent)
        self.log:PublishLog
        self.dcc = dcc
        self.setWindowTitle("Publish Manager")
        self.setMinimumSize(800, 600)
        self.resize(1000, 620)

        # ── Central widget ──
        # central = QWidget()
        # central.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._dlg_log = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Toolbar ──
        self._toolbar = ToolBar()
        self.build_log_widget()
        self._toolbar.log_requested.connect(self._show_log)
        self._toolbar.history_requested.connect(self._show_history)
        self._toolbar.settings_requested.connect(self._show_settings)
        root_layout.addWidget(self._toolbar)

        # ── Step navbar ──
        self._navbar = StepNavBar()
        root_layout.addWidget(self._navbar)

        # ── Stacked pages ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background-color: {Color.BG_DARK};")
        root_layout.addWidget(self._stack)

        # ── Build pages ──
        self._build_pages()

        # ── Loading overlay (hidden by default)
        self._loading_overlay = LoadingOverlay(self)

        # ── Apply global stylesheet ──
        self.setStyleSheet(STYLESHEET)

    # ── Page builder ──────────────────────────────────────────
    def _build_pages(self):
        # --- Page 0: Project ---
        self._project_page = ProjectSelectPage(self)
        self._project_page.project_selected.connect(self._on_project_selected)
        self._stack.addWidget(self._project_page)

        # --- Page 1: My Tasks (for selected project) ---
        self._my_task_page = MyTaskSelectPage()
        self._my_task_page.task_selected.connect(self._on_task_selected)
        self._my_task_page.skip_requested.connect(lambda: self._go_to_page(2))
        self._my_task_page.set_back_callback(lambda: self._go_to_page(0))
        self._stack.addWidget(self._my_task_page)

        # --- Page 2: Entity ---
        self._entity_page = EntitySelectPage(self)
        self._entity_page.entity_selected.connect(self._on_entity_selected)
        self._entity_page.set_back_callback(lambda: self._go_to_page(0))
        self._stack.addWidget(self._entity_page)

        # --- Page 3: Task ---
        self._task_page = TaskSelectPage()
        self._task_page.task_selected.connect(self._on_task_selected)
        self._task_page.set_back_callback(lambda: self._go_to_page(2))
        self._stack.addWidget(self._task_page)
        
        # --- Page 4: Publish Form ---
        self._form_page = PublishFormPage()
        self._form_page.proceed_to_check.connect(self._on_form_submit)
        self._form_page.set_back_callback(lambda: self._go_to_page(3))
        self._stack.addWidget(self._form_page)

        # --- Page 5: Check Panel ---
        self._check_page = CheckPanelPage()
        self._check_page.check_done.connect(self._on_check_done)
        self._check_page.go_to_publish.connect(self._on_go_to_publish)
        self._check_page.set_back_callback(lambda: self._go_to_page(4))
        self._stack.addWidget(self._check_page)

        # --- Page 6: Publish Progress ---
        self._progress_page = PublishProgressPage()
        self._progress_page.done.connect(lambda: self._go_to_page(0))
        self._progress_page.all_success.connect(self.notify_pp)
        self._stack.addWidget(self._progress_page)

        # Start at Project page
        self._stack.setCurrentIndex(0)
        self._navbar.set_current_step(0)

    def notify_pp(self):
        self._cli.notify_pp()

        
    # ── Navigation helpers ────────────────────────────────────
    def _go_to_page(self, index):
        # Require publish type before entering publish flow (pages 4+)
        if index >= 1:
            pt = self._toolbar.publish_type()
            if not pt:
                QMessageBox.warning(self, '警告', '需要先指定一下publish type！')
                return
        self._stack.setCurrentIndex(index)
        self._navbar.set_current_step(index)

    # ── Signal handlers ───────────────────────────────────────

    def _on_project_selected(self, project):
        self._selected_project: SGEntity = project
        self._toolbar.set_status(f'已选择project {project.code}')
        self.log.info(f'已选择project {project.code}')
        self._my_task_page.fill_grid(project)
        self._entity_page.fill_grid(project)
        self._go_to_page(1)

    def _on_entity_selected(self, entity_type):
        (type, id) = entity_type
        entity = SGEntity(type, id)
        self._task_page._populate(entity)
        self._toolbar.set_status(f'已选择{type}类型的 {entity.code}')
        self.log.info(f'已选择{type}类型的 {entity.code}')
        self._go_to_page(3)
        if hasattr(self, "_selected_project"):
            self._task_page.set_context(
                self._selected_project["name"],
                entity_type,
            )

    def _on_task_selected(self, task):
        self._selected_task = SGEntity('Task', task['id'])
        self.log.info(f'selected task {task["id"]}')
        pt = self._toolbar.publish_type()
        from publish_core.cli import PublishType
        publish_type_enum = PublishType(pt) if pt else PublishType.DAILY

        self._loading_overlay.show_overlay()

        self._thread = QThread(self)
        self._worker = PublishCliWorker(
            user=get_user(),
            task_id=task['id'],
            publish_type=publish_type_enum,
            widget=None,
            log=self.log,
            dcc=self.dcc
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_cli_ready)
        self._worker.error.connect(self._on_cli_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_cli_ready(self, cli):
        """Called on main thread when PublishCli (except interface) is ready.
        Rebuild the interface on the main thread with the real widget parent.
        """
        self._cli:PublishCli = cli
        self._form_page.build_info_page(self._cli)
        self._cli.init_interface_parent(self._form_page)
        if not self._cli.task_entity or not self.log:
            raise RuntimeError('can not find log or cli`s task entity!')
        self._loading_overlay.hide_overlay()
        self._go_to_page(4)
        self._toolbar.set_status(f"Task: {self._selected_task.content}")

    def _on_cli_error(self, err_msg):
        """Called on main thread when PublishCli creation fails."""
        self._loading_overlay.hide_overlay()
        QMessageBox.critical(self, "错误", f"加载任务失败:\n{err_msg}")


    def _on_form_submit(self, mode):
        if not self._cli:
            raise RuntimeError('can not find cli')
        ret = self._form_page.collect_form_info(self._cli)
        if not ret: return

        for comp in self._cli.interface.check_comps:
            comp.status = 'waiting'
        for comp in self._cli.interface.process_comps:
            comp.status = 'waiting'

        self._check_page._fill(self._cli)
        self._progress_page._fill(self._cli)

        self.log.info('form is submit!')
        if mode['mode'] == 'both':
            self._go_to_page(5)
            self._check_page._run_checks(auto=True)
        else:
            self._go_to_page(5)

        

    def _on_check_done(self, result):
        self._toolbar.set_status("Checks complete")

    def _on_go_to_publish(self, auto=False):
        self._go_to_page(6)
        if auto:
            self._progress_page.start_publish()
        self._toolbar.set_status("Publishing\u2026")

    # ── Toolbar dialogs ───────────────────────────────────────
    def build_log_widget(self):
        self._dlg_log = LogDialog(
                        parent=self
                    )
        self.log = PublishLog(self._dlg_log)


    def _show_log(self):
        if not self._dlg_log:
            raise RuntimeError('no log dialog!')
        if self._dlg_log.isHidden():
            self._dlg_log.show()



    def _show_history(self):
        task = None
        if hasattr(self, '_selected_task'): task = self._selected_task
        dlg = HistoryDialog(parent=self, task=task)
        dlg.exec()

    def _show_settings(self):
        pass