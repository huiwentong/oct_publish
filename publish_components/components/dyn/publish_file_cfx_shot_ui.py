# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'publish_file_cfx_shot.ui'
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
from qtpy.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

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
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton = QPushButton(Form)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(Form)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout.addWidget(self.pushButton_2)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"\u955c\u5934\u9636\u6bb5\u7684\u63d0\u4ea4\u4f1a\u81ea\u52a8\u62fe\u53d6\u5230lay\u9636\u6bb5\u7684component\u5e76\u5efa\u7acb\u7b49\u5f85\u586b\u5145\u7ec4\u4ef6", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"\u9009\u62e9\u6587\u4ef6\u8def\u5f84\u8fdb\u884c\u6279\u91cf\u586b\u5165", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"houdini\u5de5\u7a0b\u5185\u81ea\u52a8\u586b\u5165", None))
    # retranslateUi

