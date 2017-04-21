import logging
import multiprocessing
import sys

import cv2
import gc
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

    multiprocessing.set_start_method('spawn')

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

    num_frames = 1000
    print('frame count = ' + str(video_cap.get_frame_count()))
    cvsharpness = CVSharpness()
    sharpness_measure = cvsharpness.calculate_sharpness_video_capture(
        frame_start=0, frame_end=num_frames,
        cv_video_capture=video_cap,
        progress_tracker=progress_tracker
    )
    print(sharpness_measure.shape[0])
    result_arr = cvsharpness.test_sharpness_acceptance(sharpness_measure, frame_rate * 2, z_score=1)
    print("sharpness done")
    print("number of frames left [%d] / %d" % ((result_arr == 1).sum(), num_frames))

    # result_arr = np.ones([num_frames], dtype=np.bool_)

    correlation = CVCorrelation()
    result_arr = \
        correlation.test_correlation_video_capture(video_cap, 0.985,
                                                   result_arr,
                                                   frame_start=0,
                                                   frame_end=num_frames)

    print("correlation done")
    print("number of frames left [%d] / %d" % ((result_arr == 1).sum(), num_frames))

    # result_arr = np.ones([num_frames], dtype=np.bool_)

    # params for ShiTomasi corner detection
    feature_params = dict(maxCorners=500, qualityLevel=0.3,
                          minDistance=7, blockSize=7)
    # Parameters for lucas kanade optical flow
    lk_params = dict(winSize=(15, 15), maxLevel=2,
                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    optical_flow = CVOpticalFlow(feature_params, lk_params)
    result_arr = optical_flow.test_optical_flow_video_capture(
        video_cap, 100, result_arr, frame_start=0, frame_end=num_frames)

    print("optical flow done")
    print("number of frames left [%d] / %d" % ((result_arr == 1).sum(), num_frames))

    # Define the codec and create VideoWriter object
    codec = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename_out, codec, 2,
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

    # filtered_video_cap = CVFilteredVideoCapture(video_cap, filter_func)
    filtered_video_cap = CVVideoCapture(filename_out)

    playback_widget = VideoPlaybackWidget()
    control_widget = VideoPlaybackControlWidget(filtered_video_cap)

    frame_buffer = CVFrameBuffer(int(frame_rate * 2) + 1)

    color = np.random.randint(0, 255, (1000, 3))
    #
    #
    # def buildFrame(frame: CVFrame):
    #     frame_buffer.append(frame)
    #     prev_frame = frame_buffer.get_last(1)  # type: CVFrame
    #
    #     prev_gray = cv2.cvtColor(prev_frame.cv_mat, cv2.COLOR_BGR2GRAY)
    #     p0 = cv2.goodFeaturesToTrack(prev_gray, mask=None, **feature_params)
    #     mask = np.zeros_like(prev_frame.cv_mat)
    #
    #     frame_gray = cv2.cvtColor(frame.cv_mat, cv2.COLOR_BGR2GRAY)
    #
    #     p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, frame_gray, p0, None,
    #                                            **lk_params)
    #
    #     # Select good points
    #     good_new = p1[st == 1]
    #     good_old = p0[st == 1]
    #     displacement = (good_new - good_old) ** 2
    #     distance = np.sum(displacement, axis=1)
    #     mean_distance = distance.mean()
    #
    #     # draw the tracks
    #     new_frame_mat = frame.cv_mat
    #
    #     for i, (new, old) in enumerate(zip(good_new, good_old)):
    #         a, b = new.ravel()
    #         c, d = old.ravel()
    #         mask = cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)
    #         new_frame_mat = cv2.circle(new_frame_mat, (a, b), 5,
    #                                    color[i].tolist(), -1)
    #
    #     img = cv2.add(new_frame_mat, mask)
    #
    #     playback_widget.on_incomingFrame(CVFrame(img))

    control_widget.incomingFrame.connect(playback_widget.on_incomingFrame)
    # control_widget.incomingFrame.connect(buildFrame)

    playback_widget.show()
    control_widget.show()
    sys.exit(app.exec_())
