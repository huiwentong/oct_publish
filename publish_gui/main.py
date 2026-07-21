"""
Entry point for the publish GUI application.
"""
import sys
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt
import os
from publish_gui.ui import MainWindow


# Suppress Qt DirectWrite font fallback warnings (harmless, Windows legacy fonts)
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts.warning=false")


def run():
    """Launch the publish manager window."""
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()

