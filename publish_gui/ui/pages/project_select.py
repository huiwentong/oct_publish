"""
Page 1 - Project selection.
"""
from publish_core.database.entity import SGEntity, get_pros, get_pro_entities, get_entity_tasks, get_user
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QLayout, QSizePolicy, QScrollArea,
)
from qtpy.QtNetwork import QNetworkAccessManager, QNetworkRequest
from qtpy.QtGui import QPixmap
from qtpy.QtCore import Qt, Signal, QObject, QUrl, QRect, QSize, QPoint # type: ignore
from publish_gui.ui.theme import Color, font_header


class FlowLayout(QLayout):
    """Custom flow / wrap layout that automatically breaks into rows."""
    def __init__(self, parent=None, h_spacing=8, v_spacing=8):
        super().__init__(parent)
        self._item_list = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def _do_layout(self, rect, test_only=False):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        line_height = 0
        spacing = self._h_spacing

        for item in self._item_list:
            hint = item.sizeHint()
            next_x = x + hint.width() + spacing
            if next_x - spacing > rect.right() - m.right() and line_height > 0:
                x = rect.x() + m.left()
                y += line_height + self._v_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + spacing
            line_height = max(line_height, hint.height())

        height = y + line_height - rect.y() + m.bottom()
        return height


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
        self.setFixedSize(240, 150)
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
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(8)

        self.loader = ImageLoader()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent; border: none;")
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.loader.finished.connect(self._on_image_loaded)
        self.loader.load(project.image)
        layout.addWidget(self.image_label, stretch=1)

        code = QLabel(f"{project.code}")
        code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code.setStyleSheet(
            f"color: {Color.TEXT_SECONDARY};"
            f"background: transparent;"
            f"font-size: 10pt;"
            f"font-weight: bold;"
        )
        layout.addWidget(code)

    def _on_image_loaded(self, pixmap):
        area = self.image_label.size()
        if area.width() > 0 and area.height() > 0:
            scaled = pixmap.scaled(
                area.width(), area.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Crop to center
            x = (scaled.width() - area.width()) // 2
            y = (scaled.height() - area.height()) // 2
            if x < 0: x = 0
            if y < 0: y = 0
            cropped = scaled.copy(x, y, area.width(), area.height())
            self.image_label.setPixmap(cropped)
        else:
            scaled = pixmap.scaled(
                216, 100,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.image_label.pixmap() is not None:
            self._on_image_loaded(self.image_label.pixmap())

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        scroll_content = QWidget()
        scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._flow = FlowLayout(scroll_content, h_spacing=16, v_spacing=16)
        scroll_content.setLayout(self._flow)
        scroll.setWidget(scroll_content)

        self._cards = []
        for proj in get_pros(get_user()):
            card = ProjectCard(proj)
            card.clicked.connect(lambda p, c=card: self._on_card_clicked(p, c))
            self._cards.append(card)
            self._flow.addWidget(card)

        outer.addWidget(scroll, stretch=1)
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
        self.project_selected.emit(project)
        # for c in self._cards:
        #     c.setProperty("selected", c is card)
        #     c.style().unpolish(c)
        #     c.style().polish(c)
        # self._selected_label.setText(f"Selected: {project.code} ")
        # self._next_btn.setEnabled(True)

    def _emit_selection(self):
        if self._selected:
            self.project_selected.emit(self._selected)
