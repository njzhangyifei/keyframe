import datetime
import logging
import multiprocessing

import cv2
import sys

from cvutils import CVVideoCapture
from cvutils.cvcorrelation import CVCorrelation
from cvutils.cvopticalflow import CVOpticalFlow
from cvutils.cvprogresstracker import CVProgressTracker
from cvutils.cvsharpness import CVSharpness

def calculate_all(filename, optical_flow_distance):
    multiprocessing.set_start_method('spawn')

    filename_out = filename + '.out_%d.avi' % optical_flow_distance

    video_cap = CVVideoCapture(filename)
    frame_rate = video_cap.get_frame_rate()

    start_time = datetime.datetime.now()

    def callback(arg):
        print(arg.progress)

    progress_tracker = CVProgressTracker(callback)

    num_frames = int(video_cap.get_frame_count())
    print('frame count = ' + str(video_cap.get_frame_count()))
    cvsharpness = CVSharpness()
    sharpness_acceptance = cvsharpness.load_acceptance_file(video_cap, count=num_frames)
    if sharpness_acceptance is None:
        print('sharpness not tested, calculating')
        sharpness_measure = cvsharpness.calculate_sharpness_video_capture(
            frame_start=0, frame_end=num_frames,
            cv_video_capture=video_cap, progress_tracker=progress_tracker
        )
        sharpness_acceptance = \
            cvsharpness.test_sharpness_acceptance(sharpness_measure, frame_rate * 2, z_score=1)
        print("sharpness done")
        cvsharpness.save_acceptance_file(sharpness_acceptance, video_cap)
        print('sharpness acceptance saved')
    else:
        print('loaded sharpness acceptance')
    print("number of frames left [%d] / %d" % ((sharpness_acceptance == 1).sum(), num_frames))

    sharpness_elapsed = datetime.datetime.now() - start_time
    start_time = datetime.datetime.now()

    progress_tracker = CVProgressTracker(callback)
    cvcorrelation = CVCorrelation()
    correlation_acceptance = cvcorrelation.load_acceptance_file(video_cap, count=num_frames)
    if correlation_acceptance is None:
        print('correlation not tested, testing')
        correlation_acceptance = cvcorrelation.test_correlation_video_capture(
            video_cap, 0.985, sharpness_acceptance, frame_start=0, frame_end=num_frames, progress_tracker=progress_tracker)
        print("correlation done")
        cvcorrelation.save_acceptance_file(correlation_acceptance, video_cap)
        print('correlation acceptance saved')
    else:
        print('loaded correlation acceptance')
    print("number of frames left [%d] / %d" % ((correlation_acceptance == 1).sum(), num_frames))

    correlation_elapsed = datetime.datetime.now() - start_time
    start_time = datetime.datetime.now()

    feature_params = dict(
        maxCorners=500,
        qualityLevel=0.3,
        minDistance=7,
        blockSize=7
    )
    lk_params = dict(
        winSize=(15, 15),
        maxLevel=2,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
    )

    optical_flow = CVOpticalFlow(feature_params, lk_params)
    progress_tracker = CVProgressTracker(callback)
    result_arr = optical_flow.test_optical_flow_video_capture(
        video_cap, optical_flow_distance, correlation_acceptance,
        frame_start=0, frame_end=num_frames,
        progress_tracker=progress_tracker
    )

    print("optical flow done")
    print("number of frames left [%d] / %d" % ((result_arr == 1).sum(), num_frames))

    optical_flow_elapsed = datetime.datetime.now() - start_time

    print('sharpness    time [%f seconds]' % sharpness_elapsed.total_seconds())
    print('correlation  time [%f seconds]' % correlation_elapsed.total_seconds())
    print('optical flow time [%f seconds]' % optical_flow_elapsed.total_seconds())

    # Define the codec and create VideoWriter object
    codec = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename_out, codec, 2, (int(video_cap.get_frame_width()), int(video_cap.get_frame_height())))

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

if __name__ == '__main__':
    filename = '/home/yifei/develop/sealab/keyframe/data/GOPR7728.MP4'
    for i in range(110, 200, 10):
        calculate_all(filename, i)
    filename = '/home/yifei/develop/sealab/keyframe/data/GP017728.MP4'
    for i in range(110, 200, 10):
        calculate_all(filename, i)
