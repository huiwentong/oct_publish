"""
Page 2 - Entity type selection (Asset / Shot / Sequence).
"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame,
)
from qtpy.QtCore import Qt, Signal # type: ignore
from publish_gui.ui.theme import Color, font_header


ENTITY_TYPES = [
    {"type": "Asset", "desc": "Models, textures, rigs, etc."},
    {"type": "Shot", "desc": "Individual shots in a sequence."},
    {"type": "Sequence", "desc": "Grouped shot sequences."},
]


class EntityCard(QFrame):
    clicked = Signal(str)

    def __init__(self, info, parent=None):
        super().__init__(parent)
        self._info = info
        self.setFixedSize(220, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"EntityCard {{"
            f"  background-color: {Color.BG_CARD};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 12px;"
            f"}}"
            f"EntityCard:hover {{"
            f"  border-color: {Color.ACCENT_DIM};"
            f"  background-color: {Color.BG_HOVER};"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        name = QLabel(info["type"])
        name.setStyleSheet(
            f"color: {Color.TEXT_PRIMARY};"
            f"font-size: 14pt;"
            f"font-weight: bold;"
        )
        layout.addWidget(name)

        desc = QLabel(info["desc"])
        desc.setStyleSheet(f"color: {Color.TEXT_MUTED}; font-size: 9pt;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch()

    def mousePressEvent(self, e):
        self.clicked.emit(self._info["type"])
        super().mousePressEvent(e)


class EntitySelectPage(QWidget):
    entity_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 24, 48, 24)

        header = QLabel("Select Entity Type")
        header.setFont(font_header(18))
        header.setStyleSheet(f"color: {Color.TEXT_PRIMARY};")
        outer.addWidget(header)

        sub = QLabel("Choose the type of entity you want to publish.")
        sub.setStyleSheet(f"color: {Color.TEXT_MUTED}; font-size: 10pt;")
        outer.addWidget(sub)
        outer.addSpacing(24)

        grid = QHBoxLayout()
        grid.setSpacing(20)
        grid.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._cards = []
        for info in ENTITY_TYPES:
            card = EntityCard(info)
            card.clicked.connect(lambda t, c=card: self._on_card_clicked(t, c))
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

        self._back_btn = QPushButton("<- Back")
        self._back_btn.setObjectName("ghost")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom.addWidget(self._back_btn)

        self._next_btn = QPushButton("Next ->")
        self._next_btn.setObjectName("accent")
        self._next_btn.setEnabled(False)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._emit_selection)
        bottom.addWidget(self._next_btn)

        outer.addLayout(bottom)
        self._selected = None

    def _on_card_clicked(self, etype, card):
        self._selected = etype
        for c in self._cards:
            c.setProperty("selected", c is card)
            c.style().unpolish(c)
            c.style().polish(c)
        self._selected_label.setText(f"Selected: {etype}")
        self._next_btn.setEnabled(True)

    def _emit_selection(self):
        if self._selected:
            self.entity_selected.emit(self._selected)

    def set_back_callback(self, cb):
        self._back_btn.clicked.connect(cb)
