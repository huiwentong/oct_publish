import tempfile
from qtpy import QtCore, QtGui, QtWidgets


# Qt5 / Qt6 compatibility
try:
    WindowType = QtCore.Qt.WindowType
    WidgetAttribute = QtCore.Qt.WidgetAttribute
    MouseButton = QtCore.Qt.MouseButton
    PenStyle = QtCore.Qt.PenStyle
except AttributeError:
    WindowType = QtCore.Qt
    WidgetAttribute = QtCore.Qt
    MouseButton = QtCore.Qt
    PenStyle = QtCore.Qt


try:
    Property = QtCore.Property
except AttributeError:
    Property = QtCore.pyqtProperty


class ScreenGrabber(QtWidgets.QDialog):
    SCREEN_GRAB_CALLBACK = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self._opacity = 1
        self._click_pos = None
        self._capture_rect = QtCore.QRect()

        self.setWindowFlags(
            WindowType.FramelessWindowHint
            | WindowType.WindowStaysOnTopHint
            | WindowType.Tool
        )
        self.setAttribute(WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setMouseTracking(True)

        app = QtWidgets.QApplication.instance()
        if app:
            for screen in app.screens():
                try:
                    screen.geometryChanged.connect(
                        self._fit_screen_geometry
                    )
                except AttributeError:
                    pass

            try:
                app.screenAdded.connect(self._fit_screen_geometry)
                app.screenRemoved.connect(self._fit_screen_geometry)
            except AttributeError:
                pass

    @property
    def capture_rect(self):
        return self._capture_rect

    def paintEvent(self, event):
        mouse_pos = self.mapFromGlobal(QtGui.QCursor.pos())

        click_pos = None
        if self._click_pos:
            click_pos = self.mapFromGlobal(self._click_pos)

        painter = QtGui.QPainter(self)

        painter.setBrush(
            QtGui.QColor(0, 0, 0, self._opacity)
        )
        painter.setPen(PenStyle.NoPen)
        painter.drawRect(event.rect())

        if click_pos:
            capture_rect = QtCore.QRect(
                click_pos,
                mouse_pos
            )

            painter.setCompositionMode(
                QtGui.QPainter.CompositionMode_Clear
            )
            painter.drawRect(capture_rect)
            painter.setCompositionMode(
                QtGui.QPainter.CompositionMode_SourceOver
            )

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(255, 255, 255, 80),
                1,
                PenStyle.DotLine
            )
        )

        if click_pos:
            painter.drawLine(
                event.rect().left(),
                click_pos.y(),
                event.rect().right(),
                click_pos.y()
            )
            painter.drawLine(
                click_pos.x(),
                event.rect().top(),
                click_pos.x(),
                event.rect().bottom()
            )

        painter.drawLine(
            event.rect().left(),
            mouse_pos.y(),
            event.rect().right(),
            mouse_pos.y()
        )

        painter.drawLine(
            mouse_pos.x(),
            event.rect().top(),
            mouse_pos.x(),
            event.rect().bottom()
        )

    def mousePressEvent(self, event):
        if event.button() == MouseButton.LeftButton:
            self._click_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if (
            event.button() == MouseButton.LeftButton
            and self._click_pos
        ):
            self._capture_rect = QtCore.QRect(
                self._click_pos,
                event.globalPos()
            ).normalized()
            self._click_pos = None

        self.close()

    def mouseMoveEvent(self, event):
        self.repaint()

    def showEvent(self, event):
        self._fit_screen_geometry()

        anim = QtCore.QPropertyAnimation(
            self,
            b"_opacity_anim_prop"
        )
        anim.setStartValue(self._opacity)
        anim.setEndValue(127)
        anim.setDuration(300)
        anim.setEasingCurve(
            QtCore.QEasingCurve.OutCubic
        )
        anim.start(
            QtCore.QAbstractAnimation.DeleteWhenStopped
        )

    def _set_opacity(self, value):
        self._opacity = value
        self.repaint()

    def _get_opacity(self):
        return self._opacity

    _opacity_anim_prop = Property(
        int,
        _get_opacity,
        _set_opacity
    )

    def _fit_screen_geometry(self):
        app = QtWidgets.QApplication.instance()

        rect = QtCore.QRect()

        if app:
            for screen in app.screens():
                rect = rect.united(
                    screen.geometry()
                )

        self.setGeometry(rect)

    @classmethod
    def screen_capture(cls):
        if cls.SCREEN_GRAB_CALLBACK:
            return cls.SCREEN_GRAB_CALLBACK()

        tool = ScreenGrabber()
        tool.exec()
        return get_desktop_pixmap(
            tool.capture_rect
        )


def get_desktop_pixmap(rect):
    app = QtWidgets.QApplication.instance()

    if not app:
        return QtGui.QPixmap()

    screen = app.primaryScreen()

    if not screen:
        return QtGui.QPixmap()

    return screen.grabWindow(
        0,
        rect.x(),
        rect.y(),
        rect.width(),
        rect.height()
    )


def screen_capture_file(output_path=None):
    if output_path is None:
        output_path = tempfile.NamedTemporaryFile(
            suffix=".png",
            prefix="screencapture_",
            delete=False
        ).name

    pixmap = ScreenGrabber.screen_capture()
    pixmap.save(output_path)

    return output_path, pixmap


def test_capture():
    """
    Test screen capture.
    Drag an area on screen and save screenshot.
    """
    path = screen_capture_file()
    print(f"Screenshot saved: {path}")
    QtCore.QTimer.singleShot(
        100,
        QtWidgets.QApplication.quit
    )


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    test_capture()

    sys.exit(app.exec())