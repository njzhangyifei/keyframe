# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'KeyframeMainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_KeyframeMainWindow(object):
    def setupUi(self, KeyframeMainWindow):
        KeyframeMainWindow.setObjectName("KeyframeMainWindow")
        KeyframeMainWindow.resize(500, 426)
        KeyframeMainWindow.setMinimumSize(QtCore.QSize(500, 0))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/keyframe_icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        KeyframeMainWindow.setWindowIcon(icon)
        KeyframeMainWindow.setIconSize(QtCore.QSize(36, 36))
        self.centralwidget = QtWidgets.QWidget(KeyframeMainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_logo = QtWidgets.QHBoxLayout()
        self.horizontalLayout_logo.setObjectName("horizontalLayout_logo")
        self.label_logo = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_logo.sizePolicy().hasHeightForWidth())
        self.label_logo.setSizePolicy(sizePolicy)
        self.label_logo.setMaximumSize(QtCore.QSize(250, 250))
        self.label_logo.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label_logo.setText("")
        self.label_logo.setPixmap(QtGui.QPixmap(":/keyframe_text.png"))
        self.label_logo.setScaledContents(True)
        self.label_logo.setAlignment(QtCore.Qt.AlignCenter)
        self.label_logo.setObjectName("label_logo")
        self.horizontalLayout_logo.addWidget(self.label_logo)
        self.verticalLayout_2.addLayout(self.horizontalLayout_logo)
        self.label_text = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_text.sizePolicy().hasHeightForWidth())
        self.label_text.setSizePolicy(sizePolicy)
        self.label_text.setLineWidth(1)
        self.label_text.setAlignment(QtCore.Qt.AlignCenter)
        self.label_text.setObjectName("label_text")
        self.verticalLayout_2.addWidget(self.label_text)
        self.pushButton_load = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_load.setObjectName("pushButton_load")
        self.verticalLayout_2.addWidget(self.pushButton_load)
        self.pushButton_help = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_help.setObjectName("pushButton_help")
        self.verticalLayout_2.addWidget(self.pushButton_help)
        self.pushButton_exit = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_exit.setObjectName("pushButton_exit")
        self.verticalLayout_2.addWidget(self.pushButton_exit)
        KeyframeMainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(KeyframeMainWindow)
        QtCore.QMetaObject.connectSlotsByName(KeyframeMainWindow)

    def retranslateUi(self, KeyframeMainWindow):
        _translate = QtCore.QCoreApplication.translate
        KeyframeMainWindow.setWindowTitle(_translate("KeyframeMainWindow", "Keyframe"))
        self.label_text.setText(_translate("KeyframeMainWindow", "<html><head/><body><p align=\"center\">A simple tool for selecting keyframes from SfM videos<br/><br/></p></body></html>"))
        self.pushButton_load.setText(_translate("KeyframeMainWindow", "Load Video File"))
        self.pushButton_help.setText(_translate("KeyframeMainWindow", "Help"))
        self.pushButton_exit.setText(_translate("KeyframeMainWindow", "Exit"))

from . import KeyframeMainWindow_rc
