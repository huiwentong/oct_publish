"""
Loading overlay widget - shown during blocking operations.
"""
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel
from qtpy.QtCore import Qt, QTimer, QRect
from qtpy.QtGui import QPainter, QColor, QFont, QPen, QPainterPath

from publish_gui.ui.theme import Color, font_header


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with 'Please wait' spinner."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

        # Block mouse interactions while visible
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel("请稍后...")
        self._label.setFont(font_header(18))
        self._label.setStyleSheet(f"color: {Color.TEXT_PRIMARY}; background: transparent;")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

        self.hide()

    def resizeEvent(self, event):
        """Auto-resize to match parent when the parent resizes."""
        parent = self.parent()
        if parent:
            self.resize(parent.size())
        super().resizeEvent(event)

    def show_overlay(self):
        """Resize to parent, show, and start spinner animation."""
        parent = self.parent()
        if parent:
            self.resize(parent.size())
        self._angle = 0
        self._timer.start(50)  # 50 ms per frame
        self.show()
        self.raise_()
        # Force immediate paint so the overlay is visible before a blocking op
        from qtpy.QtWidgets import QApplication
        QApplication.processEvents()

    def hide_overlay(self):
        """Stop spinner and hide overlay."""
        self._timer.stop()
        self.hide()

    def _rotate(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        """Draw semi-transparent background and arc spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent dark background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))

        # Draw spinner arc (animated)
        center = self.rect().center()
        spinner_radius = 28
        pen_width = 4

        pen = QPen(QColor(Color.ACCENT))
        pen.setWidth(pen_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Save state, translate to spinner center, rotate, then draw
        painter.save()
        painter.translate(center.x(), center.y() -60)
        painter.rotate(self._angle)
        rect = QRect(-spinner_radius, -spinner_radius,
                     2 * spinner_radius, 2 * spinner_radius)
        # Draw only 3/4 of the arc for a spinning effect
        painter.drawArc(rect, 0, 270 * 16)
        painter.restore()

        painter.end()
