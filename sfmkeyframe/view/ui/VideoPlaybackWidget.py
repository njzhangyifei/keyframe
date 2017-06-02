# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'VideoPlaybackWidget.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_VideoPlaybackWidget(object):
    def setupUi(self, VideoPlaybackWidget):
        VideoPlaybackWidget.setObjectName("VideoPlaybackWidget")
        VideoPlaybackWidget.resize(1000, 600)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/keyframe_icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        VideoPlaybackWidget.setWindowIcon(icon)
        self.gridLayout = QtWidgets.QGridLayout(VideoPlaybackWidget)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBoxVideo = QtWidgets.QGroupBox(VideoPlaybackWidget)
        self.groupBoxVideo.setObjectName("groupBoxVideo")
        self.verticalLayout_groupBox = QtWidgets.QVBoxLayout(self.groupBoxVideo)
        self.verticalLayout_groupBox.setObjectName("verticalLayout_groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_groupBox.addLayout(self.verticalLayout)
        self.horizontalLayout_control = QtWidgets.QHBoxLayout()
        self.horizontalLayout_control.setObjectName("horizontalLayout_control")
        self.horizontalLayout_right = QtWidgets.QHBoxLayout()
        self.horizontalLayout_right.setObjectName("horizontalLayout_right")
        self.horizontalLayout_control.addLayout(self.horizontalLayout_right)
        self.horizontalLayout_left = QtWidgets.QHBoxLayout()
        self.horizontalLayout_left.setObjectName("horizontalLayout_left")
        self.label_status = QtWidgets.QLabel(self.groupBoxVideo)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_status.sizePolicy().hasHeightForWidth())
        self.label_status.setSizePolicy(sizePolicy)
        self.label_status.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_status.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_status.setObjectName("label_status")
        self.horizontalLayout_left.addWidget(self.label_status)
        self.horizontalLayout_control.addLayout(self.horizontalLayout_left)
        self.verticalLayout_groupBox.addLayout(self.horizontalLayout_control)
        self.gridLayout.addWidget(self.groupBoxVideo, 0, 0, 1, 1)

        self.retranslateUi(VideoPlaybackWidget)
        QtCore.QMetaObject.connectSlotsByName(VideoPlaybackWidget)

    def retranslateUi(self, VideoPlaybackWidget):
        _translate = QtCore.QCoreApplication.translate
        VideoPlaybackWidget.setWindowTitle(_translate("VideoPlaybackWidget", "Video Playback"))
        self.groupBoxVideo.setTitle(_translate("VideoPlaybackWidget", "Video Playback"))
        self.label_status.setText(_translate("VideoPlaybackWidget", "Status"))

from . import KeyframeMainWindow_rc
