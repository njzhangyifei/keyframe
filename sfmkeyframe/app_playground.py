import sys

import cv2
from PyQt5 import QtCore

from PyQt5.QtWidgets import QFileDialog, QMainWindow, QHBoxLayout, QVBoxLayout, \
    QWidget, QSplitter, QApplication

from cvutils.cvprogresstracker import CVProgressTracker
from cvutils.cvsharpness import CVSharpness
from cvutils.cvvideocapture import CVVideoCapture
from sfmkeyframe.view.VideoPlaybackControlWidget import \
    VideoPlaybackControlWidget
from sfmkeyframe.view.VideoPlaybackWidget import VideoPlaybackWidget


def select_file():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    filename, filter_type = dlg.getOpenFileNames()
    return filename


def get_video_cap(filename):
    print('Opening ' + filename)
    video_cap = cv2.VideoCapture(filename)
    frame_rate = video_cap.get(cv2.CAP_PROP_FPS)
    print('Frame rate = ' + str(frame_rate))
    return video_cap, frame_rate


class SharpnessViewer(QMainWindow):
    def __init__(self, parent=None):
        super(SharpnessViewer, self).__init__()
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.splitter = QSplitter(QtCore.Qt.Vertical)
        self.splitter.addWidget(VideoPlaybackWidget())
        self.splitter.addWidget(VideoPlaybackWidget())
        self.vbox_layout = QVBoxLayout()
        self.vbox_layout.addWidget(self.splitter)
        self.centralWidget.setLayout(self.vbox_layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # ex = SharpnessViewer(app)
    # ex.show()
    # filename = select_file()[0]
    filename = 'C:/Users/Yifei/unixhome/develop/sealab/keyframe/data/GP017728.MP4'
    # filename = '/home/yifei/develop/sealab/keyframe/data/GP027728.MP4'
    video_cap, frame_rate = get_video_cap(filename)
    video_cap = CVVideoCapture(video_cap)


    def callback(arg):
        print(arg.progress)


    progress_tracker = CVProgressTracker(callback)

    cvsharpness = CVSharpness()
    sharpness_measure = cvsharpness.calculate_sharpness_video_capture(
        frame_start=0, frame_end=100,
        cv_video_capture=video_cap, progress_tracker=progress_tracker)
    print(sharpness_measure.shape[0])
    sharpness_result = cvsharpness.test_sharpness_acceptance(
        sharpness_measure, frame_rate)
    print((sharpness_result == 1).sum())

    playback_widget = VideoPlaybackWidget()
    control_widget = VideoPlaybackControlWidget(video_cap)
    control_widget.incomingFrame.connect(playback_widget.on_incomingFrame)
    control_widget.show()
    playback_widget.show()

    sys.exit(app.exec_())
