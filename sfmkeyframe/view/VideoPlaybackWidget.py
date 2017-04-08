from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QGroupBox

from cvutils import CVFrame
from .VideoWidget import VideoWidget
from .ui.VideoPlaybackWidget import Ui_VideoPlaybackWidget


class VideoPlaybackWidget(QGroupBox):
    def __init__(self, *args):
        super(VideoPlaybackWidget, self).__init__(*args)
        self.ui = Ui_VideoPlaybackWidget()
        self.ui.setupUi(self)
        self.videoWidget = VideoWidget(self.ui.groupBoxVideo)
        self.ui.verticalLayout.addWidget(self.videoWidget)
        self.running = False

    def closeEvent(self, QCloseEvent):
        if self.videoWidget:
            self.videoWidget.closeEvent(QCloseEvent)
        super(VideoPlaybackWidget, self).closeEvent(QCloseEvent)

    @property
    def frame(self):
        return self.videoWidget.frame

    @frame.setter
    def frame(self, frame):
        self.videoWidget.frame = frame
        self.videoWidget.update_frame()

    @pyqtSlot(CVFrame)
    def on_incomingFrame(self, frame):
        self.frame = frame

    def update_status(self, status):
        prefix = ''
        if self.videoWidget.active:
            prefix += '[live]'
        prefix += status
        self.ui.label_status.setText(prefix)


