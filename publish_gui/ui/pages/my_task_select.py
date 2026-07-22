"""
Page 0 - My Tasks
"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QFrame,
)
from qtpy.QtCore import Qt, Signal, QSize # type: ignore
from publish_gui.ui.theme import Color, font_header
from publish_core.database.entity import get_my_project_tasks, SGEntity
from publish_gui.ui.pages.task_select import TaskItemWidget as MyTaskItemWidget


# class MyTaskItemWidget(QWidget):
#     def __init__(self, task:dict, parent=None):
#         super().__init__(parent)
#         self._task = task
#         self.setFixedHeight(52)
#         self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
#         self.setStyleSheet(
#             f"TaskItemWidget {{"
#             f"  background: transparent;"
#             f"  border: none;"
#             f"  border-bottom: 1px solid {Color.BORDER};"
#             f"}}"
#         )

#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(16, 8, 16, 8)
#         layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

#         entity_info = task.get("entity", {})
#         entity_name = entity_info.get("name", "") if isinstance(entity_info, dict) else ""

#         name = QLabel(task['content'])
#         name.setStyleSheet(
#             f"color: {Color.TEXT_PRIMARY};"
#             f"background: transparent;"
#             f"font-weight: bold;"
#             f"font-size: 11pt;"
#         )
#         layout.addWidget(name)
#         layout.addStretch()
        
#         lv_text = task['sg_latestversion']['name'] if task['sg_latestversion'] else 'no published version'
#         last_version = QLabel(lv_text)
#         last_version.setStyleSheet(
#             f"color: {Color.TEXT_SECONDARY};"
#             f"background: transparent;"
#             f"font-weight: bold;"
#             f"font-size: 11pt;"
#         )
#         layout.addWidget(last_version)
#         # layout.addStretch()

#         step = QLabel(task['step']['name'])
#         step.setStyleSheet(
#             f"color: {Color.TEXT_SECONDARY};"
#             f"background: transparent;"
#             f"border: 1px solid {Color.BORDER};"
#             f"border-radius: 10px;"
#             f"padding: 2px 10px;"
#             f"font-size: 9pt;"
#         )
#         layout.addWidget(step)

#         badge = QLabel(f"  {task['sg_status_list']}  ")
#         badge.setStyleSheet(
#             f"color: {Color.TEXT_SECONDARY};"
#             f"background: transparent;"
#             f"border: 1px solid {Color.BORDER};"
#             f"border-radius: 10px;"
#             f"padding: 2px 10px;"
#             f"font-size: 9pt;"
#         )
#         layout.addWidget(badge)

#     @property
#     def task(self):
#         return self._task


class MyTaskSelectPage(QWidget):
    task_selected = Signal(dict)
    skip_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 24, 48, 24)

        header = QLabel("My Tasks")
        header.setFont(font_header(18))
        header.setStyleSheet(f"color: {Color.TEXT_PRIMARY};")
        outer.addWidget(header)
        outer.addSpacing(16)

        self._list = QListWidget()
        self._list.setStyleSheet(
            f"QListWidget {{"
            f"  background-color: {Color.BG_LIGHT};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 10px;"
            f"  padding: 4px;"
            f"}}"
            f"QListWidget::item {{"
            f"  border: none;"
            f"  padding: 0;"
            f"}}"
            f"QListWidget::item:selected {{"
            f"  background-color: {Color.ACCENT_DIM};"
            f"  border-radius: 8px;"
            f"}}"
        )
        # self._populate()
        # self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        # self._list.setSelectionBehavior(QListWidget.SelectionBehavior.SelectItems)
        # self._list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        
        outer.addWidget(self._list)

        bottom = QHBoxLayout()
        self._selected_label = QLabel("")
        self._selected_label.setStyleSheet(f"color: {Color.TEXT_SECONDARY};")
        bottom.addWidget(self._selected_label)
        bottom.addStretch()


        self._back_btn = QPushButton("<- Back")
        self._back_btn.setObjectName("ghost")
        self._back_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom.addWidget(self._back_btn)


        self._skip_btn = QPushButton("Skip - Browse All Projects ->")
        self._skip_btn.setObjectName("ghost")
        self._skip_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._skip_btn.clicked.connect(lambda: self.skip_requested.emit())
        bottom.addWidget(self._skip_btn)

        self._next_btn = QPushButton("Go to Check ->")
        self._next_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._next_btn.setObjectName("accent")
        self._next_btn.setEnabled(False)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._emit_selection)
        bottom.addWidget(self._next_btn)

        outer.addLayout(bottom)

        self._selected = None
        # self._go_back = Signal()

    def fill_grid(self, project: SGEntity):
        self._list.clear()
        for task in get_my_project_tasks(project):
            item = QListWidgetItem()
            widget = MyTaskItemWidget(task)
            item.setSizeHint(QSize(0, 52))
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)
        self._list.clearSelection()
        


    def _on_selection_changed(self, current, previous):
        print(current)
        print(previous)
        if current is None:
            self._selected = None
            self._next_btn.setEnabled(False)
            self._selected_label.setText("")
            return
        widget = self._list.itemWidget(current)
        self._selected = widget.task #type: ignore
        self._selected_label.setText(f"Selected: {widget.task['content']}") #type: ignore
        self._next_btn.setEnabled(True)

    def _emit_selection(self):
        if self._selected:
            self.task_selected.emit(self._selected)

    def set_back_callback(self, cb):
        self._back_btn.clicked.connect(cb)



