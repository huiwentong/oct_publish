"""Modern theme constants for publish GUI"""

from qtpy.QtGui import QColor, QFont



class Color:

    BG_DARK = "#1a1c23"

    BG_MID = "#22252e"

    BG_LIGHT = "#2b2f3a"

    BG_CARD = "#2f3340"

    BG_HOVER = "#383d4b"

    SURFACE = "#262a34"

    SURFACE_HOVER = "#313644"

    ACCENT = "#6c8cff"

    ACCENT_HOVER = "#8ba3ff"

    ACCENT_DIM = "#4a6bcc"

    SUCCESS = "#4cd964"

    SUCCESS_DIM = "#2fa84b"

    WARNING = "#ff9f0a"

    WARNING_DIM = "#cc7f08"

    DANGER = "#ff453a"

    DANGER_DIM = "#cc372f"

    TEXT_PRIMARY = "#f0f1f4"

    TEXT_SECONDARY = "#9ca0b0"

    TEXT_MUTED = "#636878"

    BORDER = "#383d4b"

    BORDER_LIGHT = "#434857"

    SCROLLBAR_BG = "#1e2129"

    SCROLLBAR_FG = "#3d4354"



def font_header(size=14, weight=QFont.Weight.Bold):

    f = QFont()

    f.setPointSize(size)

    f.setWeight(weight)

    f.setFamily("Segoe UI Variable, Segoe UI, -apple-system, sans-serif")

    return f



def font_body(size=10):

    f = QFont()

    f.setPointSize(size)

    f.setFamily("Segoe UI Variable, Segoe UI, -apple-system, sans-serif")

    return f



def font_mono(size=10):

    f = QFont()

    f.setPointSize(size)

    f.setFamily("Cascadia Code, JetBrains Mono, Consolas, monospace")

    return f



STYLESHEET = """/* Global */

QWidget {

    background-color: #1a1c23;

    color: #f0f1f4;

    font-family: "Segoe UI Variable", "Segoe UI", -apple-system, sans-serif;

    font-size: 10pt;

}

QDialog {

    background-color: #1a1c23;

    color: #f0f1f4;

    font-family: "Segoe UI Variable", "Segoe UI", -apple-system, sans-serif;

    font-size: 10pt;

}

QToolTip {

    background-color: #313644;

    color: #f0f1f4;

    border: 1px solid #383d4b;

    border-radius: 6px;

    padding: 6px 10px;

}

QPushButton {

    background-color: #262a34;

    color: #f0f1f4;

    border: 1px solid #383d4b;

    border-radius: 8px;

    padding: 8px 20px;

    font-size: 10pt;

}

QPushButton:hover {

    background-color: #313644;

    border-color: #4a6bcc;

}

QPushButton:pressed {

    background-color: #383d4b;

}

QPushButton:disabled {

    color: #636878;

    background-color: #22252e;

    border-color: #383d4b;

}

QPushButton#accent {

    background-color: #6c8cff;

    color: #ffffff;

    border: none;

    font-weight: bold;

}

QPushButton#accent:hover {

    background-color: #8ba3ff;

}

QPushButton#accent:disabled {

    background-color: #4a6bcc;

    color: rgba(255,255,255,0.5);

}

QPushButton#success {

    background-color: #2fa84b;

    color: #ffffff;

    border: none;

    font-weight: bold;

}

QPushButton#success:hover {

    background-color: #4cd964;

}

QPushButton#ghost {

    background: transparent;

    border: 1px solid #383d4b;

    color: #9ca0b0;

}

QPushButton#ghost:hover {

    border-color: #4a6bcc;

    color: #f0f1f4;

}

QLineEdit, QTextEdit, QPlainTextEdit {

    background-color: #2b2f3a;

    color: #f0f1f4;

    border: 1px solid #383d4b;

    border-radius: 8px;

    padding: 8px 12px;

    selection-background-color: #4a6bcc;

}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {

    border-color: #6c8cff;

}

QComboBox {

    background-color: #2b2f3a;

    color: #f0f1f4;

    border: 1px solid #383d4b;

    border-radius: 8px;

    padding: 8px 12px;

}

QComboBox:hover {

    border-color: #4a6bcc;

}

QComboBox QAbstractItemView {

    background-color: #262a34;

    color: #f0f1f4;

    border: 1px solid #383d4b;

    border-radius: 6px;

    selection-background-color: #4a6bcc;

}

QListWidget, QTreeWidget, QTableWidget {

    background-color: #2b2f3a;

    color: #f0f1f4;

    border: 1px solid #383d4b;

    border-radius: 8px;

    outline: none;

}

QListWidget::item, QTreeWidget::item, QTableWidget::item {

    padding: 8px 12px;

    border-radius: 4px;

}

QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {

    background-color: #4a6bcc;

    color: #ffffff;

}

QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover {

    background-color: #313644;

}

QScrollBar:vertical {

    background: #1e2129;

    width: 8px;

    border-radius: 4px;

}

QScrollBar::handle:vertical {

    background: #3d4354;

    min-height: 30px;

    border-radius: 4px;

}

QScrollBar::handle:vertical:hover {

    background: #434857;

}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {

    background: #1e2129;

    height: 8px;

    border-radius: 4px;

}

QScrollBar::handle:horizontal {

    background: #3d4354;

    min-width: 30px;

    border-radius: 4px;

}

QScrollBar::handle:horizontal:hover {

    background: #434857;

}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QGroupBox {

    background-color: #22252e;

    border: 1px solid #383d4b;

    border-radius: 10px;

    margin-top: 20px;

    padding: 16px;

    font-weight: bold;

}

QGroupBox::title {

    subcontrol-origin: margin;

    subcontrol-position: top left;

    padding: 4px 12px;

    color: #9ca0b0;

}

QProgressBar {

    background-color: #2b2f3a;

    border: none;

    border-radius: 6px;

    height: 8px;

    text-align: center;

    font-size: 9pt;

    color: #f0f1f4;

}

QProgressBar::chunk {

    background-color: #6c8cff;

    border-radius: 6px;

}

QCheckBox { spacing: 8px; }

QCheckBox::indicator {

    width: 18px; height: 18px;

    border-radius: 4px;

    border: 2px solid #434857;

    background: #2b2f3a;

}

QCheckBox::indicator:checked {

    background: #6c8cff;

    border-color: #6c8cff;

}

QListWidget { background-color: #2b2f3a; border: 1px solid #383d4b; border-radius: 6px;}
QListWidget::item {
padding: 4px 8px;
}
QListWidget::item:selected {
background-color: #4a6bcc;
}
QListWidget::item:focus {
outline: none;
}
QScrollBar:vertical {
background: transparent;
width: 8px;
margin: 0;
}
QScrollBar::handle:vertical {
background: #383d4b;
border-radius: 4px;
min-height: 30px;
}
QScrollBar::handle:vertical:hover {
background: #636878;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
height: 0;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
background: transparent;
}
QScrollBar:horizontal {
background: transparent;
height: 8px;
margin: 0;
}
QScrollBar::handle:horizontal {
background: #383d4b;
border-radius: 4px;
min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
background: #636878;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
width: 0;
height: 0;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
background: transparent;
}

"""