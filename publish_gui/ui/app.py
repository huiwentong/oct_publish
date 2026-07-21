"""
Main publish window – orchestrates all wizard pages via QStackedWidget.
"""
from qtpy.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
)
from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QIcon

from publish_gui.ui.theme import Color, STYLESHEET
from publish_gui.ui.widgets import StepNavBar, ToolBar
from publish_gui.ui.dialogs import LogDialog, HistoryDialog
from publish_gui.ui.pages import (
    ProjectSelectPage,
    EntitySelectPage,
    TaskSelectPage,
    PublishFormPage,
    CheckPanelPage,
    PublishProgressPage,
)


class MainWindow(QMainWindow):
    """Root application window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Publish Manager")
        self.setMinimumSize(1024, 768)
        self.resize(1280, 860)

        # ── Central widget ──
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
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
        # Page 0: Project
        self._project_page = ProjectSelectPage()
        self._project_page.project_selected.connect(self._on_project_selected)
        self._stack.addWidget(self._project_page)
        return
        # Page 1: Entity
        self._entity_page = EntitySelectPage()
        # self._entity_page.entity_selected.connect(self._on_entity_selected)
        # self._entity_page.set_back_callback(lambda: self._go_to_page(0))
        self._stack.addWidget(self._entity_page)

        # Page 2: Task
        self._task_page = TaskSelectPage()
        # self._task_page.task_selected.connect(self._on_task_selected)
        # self._task_page.set_back_callback(lambda: self._go_to_page(1))
        self._stack.addWidget(self._task_page)

        # Page 3: Publish Form
        self._form_page = PublishFormPage()
        # self._form_page.proceed_to_check.connect(self._on_form_submit)
        # self._form_page.set_back_callback(lambda: self._go_to_page(2))
        self._stack.addWidget(self._form_page)

        # Page 4: Check Panel
        self._check_page = CheckPanelPage()
        # self._check_page.check_done.connect(self._on_check_done)
        # self._check_page.go_to_publish.connect(self._on_go_to_publish)
        self._check_page.set_back_callback(lambda: self._go_to_page(3))
        self._stack.addWidget(self._check_page)

        # Page 5: Publish Progress
        self._progress_page = PublishProgressPage()
        self._progress_page.done.connect(lambda: self._go_to_page(0))
        self._stack.addWidget(self._progress_page)

        # Start at project page
        self._stack.setCurrentIndex(0)
        self._navbar.set_current_step(0)

    # ── Navigation helpers ────────────────────────────────────
    def _go_to_page(self, index):
        self._stack.setCurrentIndex(index)
        self._navbar.set_current_step(index)

    # ── Signal handlers ───────────────────────────────────────
    def _on_project_selected(self, project):
        self._selected_project = project
        self._go_to_page(1)

    def _on_entity_selected(self, entity_type):
        self._selected_entity = entity_type
        self._go_to_page(2)
        if hasattr(self, "_selected_project"):
            self._task_page.set_context(
                self._selected_project["name"],
                entity_type,
            )

    def _on_task_selected(self, task):
        self._selected_task = task
        self._go_to_page(3)
        self._toolbar.set_status(f"Task: {task['name']}")

    def _on_form_submit(self, form_data):
        self._form_data = form_data
        self._go_to_page(4)
        if form_data.get("mode") == "publish" or form_data.get("mode") == "both":
            pass  # check first, then publish later
        self._check_page._run_checks()

    def _on_check_done(self, result):
        self._toolbar.set_status("Checks complete")

    def _on_go_to_publish(self, _):
        self._go_to_page(5)
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