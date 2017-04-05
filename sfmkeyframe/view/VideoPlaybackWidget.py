from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from .VideoWidget import VideoWidget
from .ui.VideoPlaybackWidget import Ui_VideoPlaybackWidget


class VideoPlaybackWidget(QWidget):
    def __init__(self, get_frame_func=None, frame_rate=0, *args, **kwargs):
        super(VideoPlaybackWidget, self).__init__(*args, **kwargs)
        self.ui = Ui_VideoPlaybackWidget()
        self.ui.setupUi(self)
        self.videoWidget = VideoWidget(frame_rate, self.ui.groupBoxVideo)
        self.get_frame_func = get_frame_func
        self.ui.verticalLayout.addWidget(self.videoWidget)
        self.ui.pushButton_pause.clicked.connect(self.pushButton_pause_clicked)
        self.videoWidget.timerStatusChanged.connect(
            self.video_widget_timer_status_changed)
        self.running = False

    @property
    def get_frame_func(self):
        return self.videoWidget.get_frame_func

    @get_frame_func.setter
    def get_frame_func(self, func):
        if func and func.__call__:
            self.videoWidget.get_frame_func = func

    @property
    def frame_rate(self):
        return self.videoWidget.frame_rate

    @frame_rate.setter
    def frame_rate(self, frame_rate):
        self.videoWidget.set_frame_rate(frame_rate)

    def video_widget_timer_status_changed(self, status):
        print(status)
        self.ui.pushButton_pause.setText(('Pause' if status else 'Start')
                                         + ' Update')
        self.update_status('')

    def closeEvent(self, QCloseEvent):
        if self.videoWidget:
            self.videoWidget.closeEvent(QCloseEvent)
        super(VideoPlaybackWidget, self).closeEvent(QCloseEvent)

    def pushButton_pause_clicked(self):
        if self.videoWidget.active:
            self.videoWidget.stop()
        else:
            self.videoWidget.start()

    def update_status(self, status):
        prefix = ''
        if self.videoWidget.active:
            prefix += '[live]'
        prefix += status
        self.ui.label_status.setText(prefix)


