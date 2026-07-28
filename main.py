"""
Entry point for the publish GUI application.
Sets up tray icon and window icon from resource/logl.png.
"""
import sys
import os

from qtpy.QtWidgets import QApplication, QSystemTrayIcon
from qtpy.QtGui import QIcon

from publish_gui.ui import MainWindow

os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts.warning=false")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Publish Manager")

    icon_path = os.path.join(os.path.dirname(__file__), "resource", "logl.png")
    icon = QIcon(icon_path)

    app.setWindowIcon(icon)

    tray = QSystemTrayIcon(icon, parent=app)
    tray.setToolTip("Publish Manager")
    tray.show()

    window = MainWindow()
    window.setWindowIcon(icon)

    screen = app.primaryScreen()
    if screen:
        center = screen.availableGeometry().center()
        frame = window.frameGeometry()
        frame.moveCenter(center)
        window.move(frame.topLeft())

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
