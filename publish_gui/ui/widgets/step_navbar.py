"""
Step navigation bar – shows which wizard step the user is on.
"""
from qtpy.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy
from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QPainter, QColor, QFont
from publish_gui.ui.theme import Color, font_body


_STEPS = [
    ("🎪", "Project"),
    ("📙", "My Tasks"),
    ("🧵", "Entity"),
    ("📚", "Task"),
    ("📄", "Form"),
    ("🔍", "Check"),
    ("🎯", "Publish"),
    ("🎉", "Done"),
]


class StepIndicator(QFrame):
    """Single step circle + label."""

    def __init__(self, icon, text, active=False, completed=False, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._text = text
        self._active = active
        self._completed = completed
        self.setFixedSize(100, 72)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_active(self, active):
        self._active = active
        self.update()

    def set_completed(self, completed):
        self._completed = completed
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = 50, 28
        r = 18

        # ── Circle ──
        if self._completed:
            p.setBrush(QColor(Color.SUCCESS))
            p.setPen(Qt.PenStyle.NoPen)
        elif self._active:
            p.setBrush(QColor(Color.ACCENT))
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QColor(Color.SURFACE))
            p.setPen(QColor(Color.BORDER))

        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # ── Icon / number ──
        p.setPen(QColor(Color.TEXT_PRIMARY))
        f = QFont("Segoe MDL2 Assets")
        f.setPixelSize(13)
        p.setFont(f)
        p.drawText(cx - 8, cy + 5, self._icon)

        # ── Label ──
        p.setPen(QColor(
            Color.TEXT_PRIMARY if self._active or self._completed else Color.TEXT_MUTED
        ))
        p.setFont(font_body(9))
        p.drawText(0, 50, 100, 22, Qt.AlignmentFlag.AlignCenter, self._text)

        p.end()


class StepNavBar(QWidget):
    """Horizontal row of step indicators with connecting lines."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._indicators = []
        self.setFixedHeight(88)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 8, 40, 8)
        layout.setSpacing(0)

        for i, (icon, text) in enumerate(_STEPS):
            ind = StepIndicator(icon, text, active=(i == 0))
            self._indicators.append(ind)
            layout.addWidget(ind)

            if i < len(_STEPS) - 1:
                line = QWidget()
                line.setFixedHeight(2)
                line.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Fixed
                )
                line.setStyleSheet(
                    f"background-color:{Color.BORDER};"
                )

                layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch()

    def set_current_step(self, index):
        """Highlight the given step (0-based) and mark prior steps done."""
        for i, ind in enumerate(self._indicators):
            ind.set_active(i == index)
            ind.set_completed(i < index)

    @property
    def step_count(self):
        return len(_STEPS)

