import sys

import cv2
import logging
from PyQt5 import QtCore

from PyQt5.QtWidgets import QFileDialog, QMainWindow, QHBoxLayout, QVBoxLayout, \
    QWidget, QSplitter, QApplication
from multiprocessing import freeze_support

from cvutils import CVFrame
from cvutils.cvcorrelation import CVCorrelation
from cvutils.cvframebuffer import CVFrameBuffer
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
    logging.getLogger().setLevel(logging.INFO)
    logging.info('test')
    app = QApplication(sys.argv)
    # ex = SharpnessViewer(app)
    # ex.show()
    # filename = select_file()[0]
    # filename = 'C:/Users/Yifei/unixhome/develop/sealab/keyframe/data/GP017728.MP4'
    filename = '/home/yifei/develop/sealab/keyframe/data/GP017728.MP4'
    video_cap = CVVideoCapture(filename)
    frame_rate = video_cap.get_frame_rate()


    # print("frame count = %f" % video_cap.get_frame_count())
    # video_cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
    # print("pos frame" + str(video_cap.get_position_frame()))
    # frame = video_cap.read()
    # print("last frame" + str(frame.position_frame))


    def callback(arg):
        print(arg.progress)


    progress_tracker = CVProgressTracker(callback)

    cvsharpness = CVSharpness()
    sharpness_measure = cvsharpness.calculate_sharpness_video_capture(
        frame_start=0, frame_end=10000,
        batch_size=300,
        cv_video_capture=video_cap,
        progress_tracker=progress_tracker
    )
    print('frame count = ' + str(video_cap.get_frame_count()))
    print(sharpness_measure.shape[0])
    sharpness_result = cvsharpness.test_sharpness_acceptance(
        # sharpness_measure, 35, sigma_bound=0.5)
        sharpness_measure, frame_rate * 2, sigma_bound=0.5)
    print((sharpness_result == 1).sum())
    print(sharpness_result.shape[0])

    playback_widget = VideoPlaybackWidget()
    control_widget = VideoPlaybackControlWidget(video_cap)

    frame_buffer = CVFrameBuffer(int(frame_rate*2) + 1)


    def buildFrame(frame: CVFrame):
        pos = int(frame.position_frame)
        if not sharpness_result[pos]:
            return
        status_str = 'Frame [%d] ' % pos
        if pos < sharpness_result.shape[0]:
            status_str += ' sharpness [%d] ' % sharpness_measure[pos]
            status_str += 'Acc' if sharpness_result[pos] else 'Rej'
        frame_buffer.append(frame)
        if len(frame_buffer) > 50:
            frame_prev_10 = frame_buffer.get_last(1)
            frame_prev_50 = frame_buffer.get_last(50)
            corr_10 = CVCorrelation.calculate_correlation_frame(frame,
                                                                frame_prev_10)
            corr_50 = CVCorrelation.calculate_correlation_frame(frame,
                                                                frame_prev_50)
            status_str += ' correlation [-10] = %f, [-50] = %f' %\
                          (corr_10, corr_50)
            pass
        playback_widget.update_status(status_str)
        playback_widget.on_incomingFrame(frame)


    # control_widget.incomingFrame.connect(playback_widget.on_incomingFrame)
    control_widget.incomingFrame.connect(buildFrame)
    control_widget.show()
    playback_widget.show()

    sys.exit(app.exec_())
