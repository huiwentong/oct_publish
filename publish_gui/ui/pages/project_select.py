"""
Page 1 - Project selection.
"""
from publish_core.database.entity import SGEntity, get_pros, get_pro_entities, get_entity_tasks, get_user
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame,
)
from qtpy.QtNetwork import QNetworkAccessManager, QNetworkRequest
from qtpy.QtGui import QPixmap
from qtpy.QtCore import Qt, Signal, QObject, QUrl # type: ignore
from publish_gui.ui.theme import Color, font_header


MOCK_PROJECTS = [
    {"name": "Project Atlas", "code": "atlas", "type": "Production"},
    {"name": "Project Nebula", "code": "nebula", "type": "Production"},
    {"name": "Project Solstice", "code": "solstice", "type": "Production"},
    {"name": "R&D Lab", "code": "rdlab", "type": "R&D"},
    {"name": "Showreel 2026", "code": "sr2026", "type": "Showreel"},
]

class ImageLoader(QObject):

    finished = Signal(QPixmap)

    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self._finished)

    def load(self, url):
        if not url:
            return
        print(f'load {url}!')
        request = QNetworkRequest(QUrl(url))
        self.manager.get(request)

    def _finished(self, reply):
        print('has reply!')
        print(reply)
        data = reply.readAll()

        pixmap = QPixmap()
        pixmap.loadFromData(data)
        self.finished.emit(pixmap)


class ProjectCard(QFrame):
    clicked = Signal(SGEntity)

    def __init__(self, project:SGEntity, parent=None):
        super().__init__(parent)
        self._project = project
        self.setFixedSize(240, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"ProjectCard {{"
            f"  background-color: {Color.BG_CARD};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 12px;"
            f"}}"
            f"ProjectCard:hover {{"
            f"  border-color: {Color.ACCENT_DIM};"
            f"  background-color: {Color.BG_HOVER};"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)


        self.loader = ImageLoader()
        image = QLabel(project.code)

        self.loader.finished.connect(
            lambda pix: image.setPixmap(pix)
        )

        self.loader.load(project.image)
        layout.addWidget(image)

        code = QLabel(f"{project.code}  -  {project.type}")
        code.setStyleSheet(f"color: {Color.TEXT_MUTED}; font-size: 9pt;")
        layout.addWidget(code)
        layout.addStretch()

    def mousePressEvent(self, e):
        self.clicked.emit(self._project)
        super().mousePressEvent(e)


class ProjectSelectPage(QWidget):
    project_selected = Signal(SGEntity)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 24, 48, 24)

        header = QLabel("Select a Project")
        header.setFont(font_header(18))
        header.setStyleSheet(f"color: {Color.TEXT_PRIMARY};")
        outer.addWidget(header)

        sub = QLabel("Choose the project you want to publish assets / shots for.")
        sub.setStyleSheet(f"color: {Color.TEXT_MUTED}; font-size: 10pt;")
        outer.addWidget(sub)
        outer.addSpacing(16)

        grid = QHBoxLayout()
        grid.setSpacing(16)
        grid.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._cards = []
        for proj in get_pros(get_user()):
            card = ProjectCard(proj)
            card.clicked.connect(lambda p, c=card: self._on_card_clicked(p, c))
            self._cards.append(card)
            grid.addWidget(card)
        grid.addStretch()
        outer.addLayout(grid)
        outer.addStretch()

        bottom = QHBoxLayout()
        self._selected_label = QLabel("")
        self._selected_label.setStyleSheet(f"color: {Color.TEXT_SECONDARY};")
        bottom.addWidget(self._selected_label)
        bottom.addStretch()

        self._next_btn = QPushButton("Next  ->")
        self._next_btn.setObjectName("accent")
        self._next_btn.setEnabled(False)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._emit_selection)
        bottom.addWidget(self._next_btn)
        outer.addLayout(bottom)

        self._selected = None

    def _on_card_clicked(self, project, card):
        self._selected = project
        for c in self._cards:
            c.setProperty("selected", c is card)
            c.style().unpolish(c)
            c.style().polish(c)
        self._selected_label.setText(f"Selected: {project.code} ")
        self._next_btn.setEnabled(True)

    def _emit_selection(self):
        if self._selected:
            self.project_selected.emit(self._selected)
