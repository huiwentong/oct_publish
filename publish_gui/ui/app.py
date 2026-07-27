"""
Main publish window – orchestrates all wizard pages via QStackedWidget.
"""
from qtpy.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QMessageBox, QDialog
)
from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QIcon
from publish_core.cli import PublishCli, get_user
from publish_core.database.entity import SGEntity
from publish_gui.ui.theme import Color, STYLESHEET
from publish_gui.ui.widgets import StepNavBar, ToolBar
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


class MainWindow(QDialog):
    """Root application window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Publish Manager")
        self.setMinimumSize(800, 600)
        self.resize(1000, 620)
        self._cli: PublishCli | None = None

        # ── Central widget ──
        # central = QWidget()
        # central.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Toolbar ──
        self._toolbar = ToolBar()
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
        self._stack.addWidget(self._progress_page)

        # Start at Project page
        self._stack.setCurrentIndex(0)
        self._navbar.set_current_step(0)

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
    def _on_my_task_selected(self, task):
        self._selected_task = task
        self._toolbar.set_status(f"Task: {task['content']}")
        self._go_to_page(4)
        # self._check_page._run_checks()

    def _on_project_selected(self, project):
        self._selected_project: SGEntity = project
        self._toolbar.set_status(f'已选择project {project.code}')
        self._my_task_page.fill_grid(project)
        self._entity_page.fill_grid(project)
        self._go_to_page(1)

    def _on_entity_selected(self, entity_type):
        (type, id) = entity_type
        entity = SGEntity(type, id)
        self._task_page._populate(entity)
        self._toolbar.set_status(f'已选择{type}类型的 {entity.code}')
        self._go_to_page(3)
        if hasattr(self, "_selected_project"):
            self._task_page.set_context(
                self._selected_project["name"],
                entity_type,
            )

    def _on_task_selected(self, task):
        self._selected_task = SGEntity('Task', task['id'])
        pt = self._toolbar.publish_type()
        from publish_core.cli import PublishType
        publish_type_enum = PublishType(pt) if pt else PublishType.DAILY
        self._cli = PublishCli(
            user=get_user(), 
            task_id=task['id'], 
            gui=True, 
            publish_type=publish_type_enum, 
            widget=self._form_page.files_group
            )
        self._form_page.build_info_page(self._cli)
        self._go_to_page(4)
        self._toolbar.set_status(f"Task: {task['content']}")


    def _on_form_submit(self, mode):
        if not self._cli:
            raise RuntimeError('can not find cli')
        ret = self._form_page.collect_form_info(self._cli)
        if not ret: return
        self._check_page._fill(self._cli)
        self._progress_page._fill(self._cli)
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
    def _show_log(self):
        dlg = LogDialog(
            log_text="[2026-07-21 10:00:00] INFO  Publish session started\\n"
                      "[2026-07-21 10:00:05] INFO  Validating inputs\\n"
                      "[2026-07-21 10:00:08] WARN  Preview path not set\\n"
                      "[2026-07-21 10:00:10] INFO  Checks passed\\n",
            parent=self,
        )
        dlg.exec()

    def _show_history(self):
        dlg = HistoryDialog(parent=self)
        dlg.exec()

    def _show_settings(self):
        pass