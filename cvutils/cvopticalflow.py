from collections import deque

import cv2
import multiprocessing
import numpy as np
import os

from multiprocessing import Process

from cvutils import CVVideoCapture, CVFrame
from cvutils.cvprogresstracker import CVProgressTracker
from utils import stats, RepeatingTimer


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
                                      gray_scale_conversion_code,
                                      skip_window_both_end=0
                                      ):
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
            if frame_acceptance_ctype[
                int(buffer[0].position_frame - frame_start)]:
                break
            else:
                buffer.popleft()

        # greedy
        iter_buffer = iter(buffer)
        frame_initial = next(iter_buffer)
        frame_initial_gray = \
            frame_initial.get_cv_mat_grayscale(gray_scale_conversion_code)
        frame_initial_features = \
            cv2.goodFeaturesToTrack(frame_initial_gray, mask=None,
                                    **feature_params)

        frame_final = None
        frame_i_prev = None
        skipped_frame_count = 0
        mean_distance = 0
        for frame_i in iter_buffer:  # type: CVFrame
            if (frame_i.position_frame < worker_frame_start + skip_window_both_end) or \
                    (frame_i.position_frame > worker_frame_end - skip_window_both_end):
                # skip first and last frame_rate frames on each worker
                skipped_frame_count += 1
                continue
            if not frame_acceptance_ctype[int(frame_i.position_frame - frame_start)]:
                # skipped
                skipped_frame_count += 1
                continue
            frame_i_gray = frame_i.get_cv_mat_grayscale(
                gray_scale_conversion_code)
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
                break

            good_initial_features = frame_initial_features[feature_status == 1]
            good_i_features = frame_i_features[feature_status == 1]

            displacement = (good_i_features - good_initial_features) ** 2
            distance = np.sqrt(np.sum(displacement, axis=1))
            mean_distance = stats.trimboth(distance, 0.1).mean()

            if mean_distance < distance_limit:
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
        print('optical flow process [%d] matched %d -> %d, distance = %d' %
              (os.getpid(), int(frame_initial.position_frame),
               int(frame_final.position_frame), mean_distance))

        # remove unmatched
        buffer.popleft()
        for i in range(0, skipped_frame_count):
            f = buffer.popleft()  # type: CVFrame
            # special handling for greedy algorithm
            if (f.position_frame < worker_frame_start + skip_window_both_end) or \
                    (f.position_frame > worker_frame_end - skip_window_both_end):
                # skip first and last frame_rate frames on each worker
                skipped_frame_count += 1
                continue
            frame_acceptance_ctype[int(f.position_frame) - frame_start] = False

        with progress_value.get_lock():
            progress_value.value += (skipped_frame_count + 1) / frame_count


class CVOpticalFlow:
    def __init__(self, feature_params, lucas_kanade_params):
        self.feature_params = feature_params
        self.lucas_kanade_params = lucas_kanade_params
        pass

    def test_optical_flow_video_capture(self,
                                        cv_video_capture: CVVideoCapture,
                                        distance_limit,
                                        frame_acceptance_np: np.ndarray,
                                        frame_start=0, frame_end=None,
                                        batch_size=200,
                                        gray_scale_conversion_code=cv2.COLOR_BGR2GRAY,
                                        progress_tracker: CVProgressTracker = None):
        frame_count = int(cv_video_capture.get_frame_count())
        if frame_end:
            cv_video_capture.set_position_frame(frame_start)
            frame_count = min(frame_end - frame_start, frame_count)
            frame_count = max(frame_count, 0)

        if progress_tracker:
            progress_tracker.running = True

        frame_acceptance_ctype = \
            multiprocessing.Array('b', frame_acceptance_np.tolist())

        progress_value = multiprocessing.Value('d')
        progress_value.value = 0
        lock_video_capture = multiprocessing.RLock()

        worker_count = multiprocessing.cpu_count()
        task_per_worker = int(frame_count / worker_count)
        args_list = [(task_per_worker * i, task_per_worker * (i + 1),
                      frame_start, frame_count, batch_size,
                      distance_limit,
                      self.feature_params,
                      self.lucas_kanade_params,
                      frame_acceptance_ctype,
                      cv_video_capture.file_handle,
                      progress_value,
                      lock_video_capture,
                      gray_scale_conversion_code)
                     for i in range(0, worker_count - 1)]
        args_list.append((task_per_worker * (worker_count - 1), frame_count,
                          frame_start, frame_count, batch_size,
                          distance_limit,
                          self.feature_params,
                          self.lucas_kanade_params,
                          frame_acceptance_ctype,
                          cv_video_capture.file_handle,
                          progress_value,
                          lock_video_capture,
                          gray_scale_conversion_code))

        processes = [Process(target=_test_optical_flow_capture_worker,
                             args=arg_tuple) for arg_tuple in args_list]

        def update_progress_tracker():
            progress_tracker.progress = progress_value.value

        progress_timer = RepeatingTimer(0.1, update_progress_tracker)

        if progress_tracker:
            progress_timer.start()

        if progress_tracker:
            progress_tracker.running = True
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        print('final pass')
        progress_value.Value = 0
        _test_optical_flow_capture_worker(frame_start, frame_end,
                                          frame_start, frame_count,
                                          batch_size,
                                          distance_limit,
                                          self.feature_params,
                                          self.lucas_kanade_params,
                                          frame_acceptance_ctype,
                                          cv_video_capture.file_handle,
                                          progress_value,
                                          lock_video_capture,
                                          gray_scale_conversion_code)
        if progress_tracker:
            progress_timer.cancel()
            progress_tracker.complete()

        return np.array(frame_acceptance_ctype, dtype=np.bool_)
        pass
