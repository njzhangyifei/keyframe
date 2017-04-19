import logging

import sys

import cv2
from PyQt5.QtWidgets import QApplication

from cvutils import CVFrame, CVVideoCapture
from cvutils.cvcorrelation import CVCorrelation, \
    _test_correlation_capture_worker
from cvutils.cvfilteredvideocapture import CVFilteredVideoCapture
from cvutils.cvframebuffer import CVFrameBuffer
import numpy as np

from cvutils.cvopticalflow import CVOpticalFlow
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
    filename_out = 'C:/Users/Yifei/unixhome/develop/sealab/keyframe/data' \
               '/GP017728_out.avi'
    # filename = '/home/yifei/develop/sealab/keyframe/data/GP017728.MP4'
    # filename_out = '/home/yifei/develop/sealab/keyframe/data/GP017728_out.avi'
    video_cap = CVVideoCapture(filename)
    frame_rate = video_cap.get_frame_rate()


    def callback(arg):
        print(arg.progress)


    progress_tracker = CVProgressTracker(callback)

    num_frames = 2000
    cvsharpness = CVSharpness()
    sharpness_measure = cvsharpness.calculate_sharpness_video_capture(
        frame_start=0, frame_end=num_frames,
        cv_video_capture=video_cap,
        progress_tracker=progress_tracker
    )
    print('frame count = ' + str(video_cap.get_frame_count()))
    print(sharpness_measure.shape[0])
    sharpness_result = cvsharpness.test_sharpness_acceptance(

        # sharpness_measure, 35, sigma_bound=0.5)
        sharpness_measure, frame_rate * 2, z_score=1)
    print("sharpness done")
    print("number of frames left [%d]" % (sharpness_result == 1).sum())

    result_arr = sharpness_result

    # _calculate_correlation_capture_worker(
    #     0, 1000, video_cap.get_frame_count(),
    #     0.98, result_list, video_cap.file_handle, cv2.COLOR_BGR2GRAY
    # )
    correlation = CVCorrelation()
    result_arr = \
        correlation.test_correlation_video_capture(video_cap, 0.985,
                                                   result_arr,
                                                   frame_start=0,
                                                   frame_end=num_frames)
    print("correlation done")
    print("number of frames left [%d]" % (result_arr == 1).sum())

    # params for ShiTomasi corner detection
    feature_params = dict(maxCorners=500,
                          qualityLevel=0.3,
                          minDistance=7,
                          blockSize=7)
    # Parameters for lucas kanade optical flow
    lk_params = dict(winSize=(15, 15),
                     maxLevel=2,
                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                               10, 0.03))

    optical_flow = CVOpticalFlow(feature_params, lk_params)
    result_arr = \
        optical_flow.test_optical_flow_video_capture \
            (video_cap, 20, result_arr,
             frame_start=0, frame_end=num_frames)
    print("optical flow done")
    print("number of frames left [%d]" % (result_arr == 1).sum())

    # Define the codec and create VideoWriter object
    codec = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename_out, codec, video_cap.get_frame_rate(),
                          (int(video_cap.get_frame_width()),
                           int(video_cap.get_frame_height())))

    while video_cap.is_open:
        original_frame = video_cap.read()
        if original_frame is None:
            break
        pos = int(original_frame.position_frame)
        if pos < num_frames:
            if result_arr[pos]:
                out.write(original_frame.cv_mat)
        else:
            break

    out.release()


    def filter_func(frame):
        if frame is None:
            return False
        pos = int(frame.position_frame)
        return pos < num_frames and result_arr[pos]


    filtered_video_cap = CVFilteredVideoCapture(video_cap, filter_func)

    playback_widget = VideoPlaybackWidget()
    control_widget = VideoPlaybackControlWidget(filtered_video_cap)

    # frame_buffer = CVFrameBuffer(int(frame_rate * 2) + 1)

    # def buildFrame(frame: CVFrame):
    #     pos = int(frame.position_frame)
    #     if pos < num_frames and result_arr[pos]:
    #         control_widget.playback_timer.timeout.emit()
    #         playback_widget.on_incomingFrame(frame)
    #     else:
    #         playback_widget.on_incomingFrame(frame)
    #         pass

    control_widget.incomingFrame.connect(playback_widget.on_incomingFrame)
    # control_widget.incomingFrame.connect(buildFrame)

    playback_widget.show()
    control_widget.show()
    sys.exit(app.exec_())
