"""
Page 2 - Entity type selection (Asset / Shot / Sequence).
"""
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QComboBox, QCompleter
)
from qtpy.QtGui import QStandardItemModel, QStandardItem
from publish_core.database.entity import get_pro_entities, get_entity_tasks, SGEntity
from qtpy.QtCore import Qt, Signal # type: ignore
from publish_gui.ui.theme import Color, font_header
from publish_gui.ui.utils import clear_layout

ENTITY_TYPES = [
    {"type": "Asset", "desc": "Models, textures, rigs, etc."},
    {"type": "Shot", "desc": "Individual shots in a sequence."},
    {"type": "Sequence", "desc": "Grouped shot sequences."},
]


class EntityCard(QFrame):
    clicked = Signal(tuple)

    def __init__(self, type, entities, parent=None):
        super().__init__(parent)
        self._info = type
        self.setFixedSize(280, 200)
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

        name = QLabel(type)
        name.setStyleSheet(
            f"color: {Color.TEXT_PRIMARY};"
            f"background: transparent;"
            f"font-size: 40pt;"
            f"font-weight: bold;"
        )
        layout.addWidget(name)

        model = QStandardItemModel()
        for entt in entities:
            item = QStandardItem(f"{entt['code']}  |  {entt['sg_status_list']}")
            item.setData(entt['id'], Qt.ItemDataRole.UserRole)
            model.appendRow(item)


        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseSensitive)
        completer.setCompletionMode(
            QCompleter.CompletionMode.PopupCompletion
        )
        completer.setModel(model)
        self.ett_combo = QComboBox(self)
        self.ett_combo.setModel(model)
        self.ett_combo.setEditable(True)
        self.ett_combo.setCompleter(completer)
        self.ett_combo.setStyleSheet(
            f"QComboBox {{"
            f"  background-color: {Color.BG_LIGHT};"
            f"  color: {Color.TEXT_PRIMARY};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 6px;"
            f"  padding: 6px 10px 6px 10px;"
            f"  font-size: 10pt;"
            f"  min-height: 24px;"
            f"}}"
            f"QComboBox:hover {{"
            f"  border-color: {Color.ACCENT_DIM};"
            f"}}"
            f"QComboBox:focus {{"
            f"  border-color: {Color.ACCENT};"
            f"}}"
            f"QComboBox::drop-down {{"
            f"  border: none;"
            f"  width: 24px;"
            f"  subcontrol-position: top right;"
            f"  subcontrol-origin: padding;"
            f"}}"
            f"QComboBox::down-arrow {{"
            f"  border: none;"
            f"  width: 0;"
            f"  height: 0;"
            f"  border-left: 5px solid transparent;"
            f"  border-right: 5px solid transparent;"
            f"  border-top: 6px solid {Color.TEXT_SECONDARY};"
            f"}}"
            f"QComboBox QAbstractItemView {{"
            f"  background-color: {Color.SURFACE};"
            f"  color: {Color.TEXT_PRIMARY};"
            f"  border: 1px solid {Color.BORDER};"
            f"  border-radius: 6px;"
            f"  padding: 4px;"
            f"  outline: none;"
            f"  selection-background-color: {Color.ACCENT_DIM};"
            f"  selection-color: #ffffff;"
            f"}}"
            f"QComboBox QAbstractItemView::item {{"
            f"  padding: 6px 10px;"
            f"  min-height: 22px;"
            f"  border-radius: 4px;"
            f"}}"
            f"QComboBox QAbstractItemView::item:hover {{"
            f"  background-color: {Color.SURFACE_HOVER};"
            f"}}"
        )




        layout.addWidget(self.ett_combo)
        layout.addStretch()

    def mousePressEvent(self, e):
        self.clicked.emit((self._info, self.ett_combo.currentData(Qt.ItemDataRole.UserRole)))
        super().mousePressEvent(e)


class EntitySelectPage(QWidget):
    entity_selected = Signal(tuple)

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

        self._cards = []
        self.grid = QHBoxLayout()
        self.grid.setSpacing(20)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        
        outer.addLayout(self.grid)
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
        self.entity_selected.emit(etype)
        # self._selected = etype
        # for c in self._cards:
        #     c.setProperty("selected", c is card)
        #     c.style().unpolish(c)
        #     c.style().polish(c)
        # self._selected_label.setText(f"Selected: {etype}")
        # self._next_btn.setEnabled(True)

    def _emit_selection(self):
        if self._selected:
            self.entity_selected.emit(self._selected)

    def set_back_callback(self, cb):
        self._back_btn.clicked.connect(cb)


    def fill_grid(self, project:SGEntity):
        clear_layout(self.grid)
            
        
        self._cards = []
        for type, entities in get_pro_entities(project).items():
            card = EntityCard(type, entities)
            card.clicked.connect(lambda t, c=card: self._on_card_clicked(t, c))
            self._cards.append(card)
            self.grid.addWidget(card)
        self.grid.addStretch()
