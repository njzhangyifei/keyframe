from collections import deque

import cv2
import numpy as np

from cvutils import CVVideoCapture, CVFrame
from cvutils.cvprogresstracker import CVProgressTracker


def _test_optical_flow_capture_worker(worker_frame_start,
                                      worker_frame_end,
                                      frame_start, frame_count, batch_size,
                                      distance_limit,
                                      feature_params,
                                      lucas_kanade_params,
                                      frame_acceptance_ctype,
                                      file_handle,
                                      progress_value,
                                      lock_video_capture,
                                      gray_scale_conversion_code):
    video_capture = CVVideoCapture(file_handle)
    video_capture.set_position_frame(worker_frame_start)
    frame_rate = video_capture.get_frame_rate()
    buffer = deque()
    current_frame = worker_frame_start
    need_more_frame = True
    while True:
        if need_more_frame:
            # read in until the end
            if current_frame < worker_frame_end:
                amount_load = int(
                    min(batch_size, worker_frame_end - current_frame))
                with lock_video_capture:
                    buffer += [video_capture.read() for i in
                               range(0, amount_load)]
                current_frame += amount_load
                need_more_frame = False
            else:
                # no more frame?
                break

        # purge buffer until we find a possible list
        while True:
            if len(buffer) == 0:
                need_more_frame = True
                continue
            if frame_acceptance_ctype[int(buffer[0].position_frame - frame_start)]:
                break
            else:
                buffer.popleft()

        # greedy
        iter_buffer = iter(buffer)
        frame_initial = next(iter_buffer)
        frame_initial_gray = \
            frame_initial.get_cv_mat_grayscale(gray_scale_conversion_code)
        frame_initial_features = \
            cv2.goodFeaturesToTrack(frame_initial_gray, mask=None, **feature_params)

        frame_final = None
        frame_i_prev = None
        skipped_frame_count = 0
        for frame_i in iter_buffer:  # type: CVFrame
            if not frame_acceptance_ctype[int(frame_i.position_frame - frame_start)]:
                # skipped
                skipped_frame_count += 1
                continue
            frame_i_gray = frame_i.get_cv_mat_grayscale(gray_scale_conversion_code)
            frame_i_features, feature_status, err = \
                cv2.calcOpticalFlowPyrLK(frame_initial_gray, frame_i_gray,
                                         frame_initial_features,
                                         None,
                                         **lucas_kanade_params)

            num_features_left = feature_status.sum()

            if num_features_left == 0:
                # we are lost
                # set the last accept frame to get maximum distance
                frame_final = frame_i_prev
                pass

            good_initial_features = frame_initial_features[feature_status == 1]
            good_i_features = frame_i_features[feature_status == 1]

            distance = 0
            if distance < distance_limit:
                frame_i_prev = frame_i
                skipped_frame_count += 1
                continue
            frame_final = frame_i
            break

        # found the frame
        if frame_final is None:
            need_more_frame = True
            continue

        # matched
        # logging.info('proc [%d] matched %d -> %d' %
        #              (os.getpid(), int(template.position_frame), int(image.position_frame)))
        print('proc [%d] matched %d -> %d' %
              (os.getpid(), int(template.position_frame),
               int(image.position_frame)))

        # remove unmatched
        buffer.popleft()
        for i in range(0, skipped_frame_count):
            f = buffer.popleft()  # type: CVFrame
            if f.position_frame < worker_frame_end - frame_rate / 2:
                frame_acceptance_ctype[
                    int(f.position_frame) - frame_start] = False

        with progress_value.get_lock():
            progress_value.value += (skipped_frame_count + 1) / frame_count


class CVOpticalFlow():
    def __init__(self):
        pass

    @staticmethod
    def test_optical_flow_video_capture(cv_video_capture: CVVideoCapture,
                                        distance_limit,
                                        frame_acceptance_np: np.ndarray,
                                        frame_start=0, frame_end=None,
                                        batch_size=100,
                                        gray_scale_conversion_code=cv2.COLOR_BGR2GRAY,
                                        progress_tracker: CVProgressTracker = None):
        pass
