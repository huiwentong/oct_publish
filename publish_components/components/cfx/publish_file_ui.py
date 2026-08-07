# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'publish_file.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from qtpy.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from qtpy.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QLabel,
    QListWidgetItem, QPushButton, QSizePolicy, QTextEdit,
    QWidget)

from .file_list_widget import FileListWidget

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(680, 295)
        Form.setMinimumSize(QSize(680, 295))
        Form.setMaximumSize(QSize(16777215, 295))
        font = QFont()
        font.setPointSize(10)
        Form.setFont(font)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.listWidget_abc = FileListWidget(Form)
        self.listWidget_abc.setObjectName(u"listWidget_abc")
        font1 = QFont()
        font1.setFamilies([u"Consolas"])
        font1.setPointSize(10)
        self.listWidget_abc.setFont(font1)
        self.listWidget_abc.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.gridLayout.addWidget(self.listWidget_abc, 1, 1, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 1, 1, 1)

        self.pushButton_pick_abc = QPushButton(Form)
        self.pushButton_pick_abc.setObjectName(u"pushButton_pick_abc")
        self.pushButton_pick_abc.setMinimumSize(QSize(100, 25))

        self.gridLayout.addWidget(self.pushButton_pick_abc, 1, 0, 1, 1)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.textEdit = QTextEdit(Form)
        self.textEdit.setObjectName(u"textEdit")

        self.gridLayout.addWidget(self.textEdit, 2, 1, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"\u6a21\u677f\u8def\u5f84\u4e00\u822c\u4e3a\u81ea\u52a8\u586b\u5145\uff0c\u7279\u6b8a\u60c5\u51b5\u4e0b\u518d\u70b9\u51fb\u6309\u94ae\u624b\u52a8\u9009\u62e9", None))
        self.pushButton_pick_abc.setText(QCoreApplication.translate("Form", u"\u6a21\u677f\u8def\u5f84", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"\u4e0a\u6e38\u7248\u672c\u53f7", None))
    # retranslateUi

