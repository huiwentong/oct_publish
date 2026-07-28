
import sys
import os

path = r"D:\HWT\repository\newpublish\publish_gui\main.py"

content = (
    '"""\n'
    'Entry point for the publish GUI application.\n'
    'Sets up tray icon and window icon from resource/logol.png.\n'
    '"""\n'
    'import sys\n'
    'from qtpy.QtWidgets import QApplication, QSystemTrayIcon\n'
    'from qtpy.QtGui import QIcon\n'
    'import os\n'
    'from publish_gui.ui import MainWindow\n'
    '\n'
    'os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts.warning=false")\n'
    '\n'
    '\n'
    'def run():\n'
    '    """Launch the publish manager window."""\n'
    '    app = QApplication(sys.argv)\n'
    '    app.setApplicationName("Publish Manager")\n'
    '\n'
    '    icon_path = os.path.join(os.path.dirname(__file__), "resource", "logol.png")\n'
    '    icon = QIcon(icon_path)\n'
    '    app.setWindowIcon(icon)\n'
    '\n'
    '    tray = QSystemTrayIcon(icon, parent=app)\n'
    '    tray.setToolTip("Publish Manager")\n'
    '    tray.show()\n'
    '\n'
    '    window = MainWindow()\n'
    '    window.setWindowIcon(icon)\n'
    '\n'
    '    screen = app.primaryScreen()\n'
    '    if screen:\n'
    '        center = screen.availableGeometry().center()\n'
    '        frame = window.frameGeometry()\n'
    '        frame.moveCenter(center)\n'
    '        window.move(frame.topLeft())\n'
    '    window.show()\n'
    '\n'
    '    sys.exit(app.exec())\n'
    '\n'
    '\n'
    'if __name__ == "__main__":\n'
    '    run()\n'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Written OK")
