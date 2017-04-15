import logging

import sys

import cv2
from PyQt5.QtWidgets import QApplication

from cvutils import CVFrame, CVVideoCapture
from cvutils.cvcorrelation import CVCorrelation, _test_correlation_capture_worker
from cvutils.cvframebuffer import CVFrameBuffer
import numpy as np

from cvutils.cvprogresstracker import CVProgressTracker
from cvutils.cvsharpness import CVSharpness
from sfmkeyframe.view.VideoPlaybackControlWidget import \
    VideoPlaybackControlWidget
from sfmkeyframe.view.VideoPlaybackWidget import VideoPlaybackWidget

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    logging.info('test')
    app = QApplication(sys.argv)
    # ex = SharpnessViewer(app)
    # ex.show()
    # filename = select_file()[0]
    filename = 'C:/Users/Yifei/unixhome/develop/sealab/keyframe/data/GP017728.MP4'
    # filename = '/home/yifei/develop/sealab/keyframe/data/GP017728.MP4'
    video_cap = CVVideoCapture(filename)
    frame_rate = video_cap.get_frame_rate()


    def callback(arg):
        print(arg.progress)

    progress_tracker = CVProgressTracker(callback)

    # cvsharpness = CVSharpness()
    # sharpness_measure = cvsharpness.calculate_sharpness_video_capture(
    #     frame_start=0, frame_end=1000,
    #     batch_size=300,
    #     cv_video_capture=video_cap,
    #     progress_tracker=progress_tracker
    # )
    # print('frame count = ' + str(video_cap.get_frame_count()))
    # print(sharpness_measure.shape[0])
    # sharpness_result = cvsharpness.test_sharpness_acceptance(
    #     # sharpness_measure, 35, sigma_bound=0.5)
    #     sharpness_measure, frame_rate * 2, sigma_bound=0)
    # print((sharpness_result == 1).sum())
    # print(sharpness_result.shape[0])

    # result_list = sharpness_result.tolist()

    result_list = np.ones([10000], dtype=np.bool_)

    # _calculate_correlation_capture_worker(
    #     0, 1000, video_cap.get_frame_count(),
    #     0.98, result_list, video_cap.file_handle, cv2.COLOR_BGR2GRAY
    # )
    correlation = CVCorrelation()
    correlation.test_correlation_video_capture(video_cap, 0.98,
                                               result_list, 0, 2000)

    playback_widget = VideoPlaybackWidget()
    control_widget = VideoPlaybackControlWidget(video_cap)

    frame_buffer = CVFrameBuffer(int(frame_rate*2) + 1)


    def buildFrame(frame: CVFrame):
        pos = int(frame.position_frame)
        if pos < 2000 and result_list[pos]:
            control_widget.playback_timer.timeout.emit()
        else:
            playback_widget.on_incomingFrame(frame)

    # control_widget.incomingFrame.connect(playback_widget.on_incomingFrame)
    control_widget.incomingFrame.connect(buildFrame)

    playback_widget.show()
    control_widget.show()
    sys.exit(app.exec_())



