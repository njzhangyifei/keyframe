from functools import partial

import cv2
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QGroupBox

from cvutils import CVFrame
from cvutils.cvvideocapture import CVVideoCapture
from .ui.VideoPlaybackControlWidget import Ui_VideoPlaybackControlGroupBox


class VideoPlaybackControlWidget(QGroupBox):
    def __init__(self, video_capture: CVVideoCapture, *args):
        super(VideoPlaybackControlWidget, self).__init__(*args)
        self.current_frame = None
        self.ui = Ui_VideoPlaybackControlGroupBox()
        self.ui.setupUi(self)
        self.video_capture = video_capture
        self.ui.label_frameCount.text = self.video_capture.get_frame_count()
        self.playback_timer = QTimer(self)
        self.playback_timer_rate = 1000.0 / self.video_capture.get_frame_rate()
        self.playback_timer.timeout.connect(self.playback_timer_timeout)

        self.ui.pushButton_playresume.clicked.connect(
            self.pushButton_playresume_clicked
        )
        self.ui.pushButton_nextFrame.clicked.connect(
            partial(self.pushButton_Frame_clicked, val=1)
        )
        self.ui.pushButton_prevFrame.clicked.connect(
            partial(self.pushButton_Frame_clicked, val=-1)
        )
        self.ui.pushButton_nextSecond.clicked.connect(
            partial(self.pushButton_Second_clicked, val=1)
        )
        self.ui.pushButton_prevSecond.clicked.connect(
            partial(self.pushButton_Second_clicked, val=-1)
        )

        self.ui.spinBox_positionFrame.valueChanged.connect(
            self.spinBox_positionFrame_valueChanged
        )
        self.ui.horizontalSlider_positionRatio.valueChanged.connect(
            self.horizontalSlider_positionRatio_valueChanged
        )

        self.frame_callback_functions = set()

    def pushButton_playresume_clicked(self):
        if not self.playback_timer.isActive():
            self.playback_timer.start(self.playback_timer_rate)
        else:
            self.playback_timer.stop()

    def pushButton_Frame_clicked(self, val):
        position_current_frame = self.video_capture.get_position_frame() + val - 1
        position_current_frame = max(0, position_current_frame)
        position_current_frame = min(position_current_frame,
                                     self.video_capture.get_frame_count())
        self.video_capture.set_position_frame(position_current_frame)
        self.playback_timer_timeout()
        self.update_position_ui()

    def pushButton_Second_clicked(self, val):
        position_current_frame = self.video_capture.get_position_frame() + \
                                 val * self.video_capture.get_frame_rate()
        position_current_frame = max(0, position_current_frame)
        position_current_frame = min(position_current_frame,
                                     self.video_capture.get_frame_count())
        self.video_capture.set_position_frame(position_current_frame)
        self.playback_timer_timeout()
        self.update_position_ui()

    def horizontalSlider_positionRatio_valueChanged(self, val):
        total = self.video_capture.get_frame_count()
        ratio = float(self.ui.horizontalSlider_positionRatio.value()) / \
                float(self.ui.horizontalSlider_positionRatio.maximum())
        pos = round(ratio * total)
        self.video_capture.set_position_frame(int(pos))
        self.playback_timer_timeout()
        self.update_position_ui()

    def spinBox_positionFrame_valueChanged(self, val):
        self.video_capture.set_position_frame(self.ui.spinBox_positionFrame.value() - 1)
        self.playback_timer_timeout()
        self.update_position_ui()

    incomingFrame = pyqtSignal([CVFrame])

    def attach_frame_callback_function(self, func):
        if func and func.__call__:
            self.frame_callback_functions.add(func)

    def detach_frame_callback_function(self, func):
        if func in self.frame_callback_functions:
            self.frame_callback_functions.remove(func)

    def playback_timer_timeout(self):
        frame = self.video_capture.read()
        frame.cv_mat = cv2.cvtColor(frame.cv_mat, cv2.COLOR_BGR2RGB)
        if frame:
            self.current_frame = frame
            for func in self.frame_callback_functions:
                func(frame)
            self.incomingFrame.emit(frame)
        self.update_position_ui()

    def update_position_ui(self):
        pos = self.video_capture.get_position_frame()
        total = self.video_capture.get_frame_count()
        if pos is None:
            return
        ratio = float(pos) / float(total)
        self.ui.label_frameCount.blockSignals(True)
        self.ui.label_frameCount.setText(str(total))
        self.ui.label_frameCount.blockSignals(False)
        self.ui.spinBox_positionFrame.blockSignals(True)
        self.ui.spinBox_positionFrame.setMaximum(total - 1)
        self.ui.spinBox_positionFrame.setValue(pos)
        self.ui.spinBox_positionFrame.blockSignals(False)
        self.ui.horizontalSlider_positionRatio.blockSignals(True)
        self.ui.horizontalSlider_positionRatio.setValue(
            ratio * self.ui.horizontalSlider_positionRatio.maximum()
        )
        self.ui.horizontalSlider_positionRatio.blockSignals(False)
        self.update()
