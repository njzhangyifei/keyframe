from collections import deque

import cv2
import multiprocessing
import numpy as np
import os

from multiprocessing import Process

from cvutils import CVVideoCapture, CVFrame
from cvutils.cvmisc import generate_multiprocessing_final_pass_ranges
from cvutils.cvprogresstracker import CVProgressTracker
from utils import stats, RepeatingTimer, first_occurrence_index, \
    last_occurrence_index


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
    if worker_frame_start > worker_frame_end:
        return
    video_capture = CVVideoCapture(file_handle)
    video_capture.set_position_frame(worker_frame_start)
    buffer = deque()
    current_frame = worker_frame_start
    need_more_frame = True
    worker_last_candidate = None
    while True:
        if need_more_frame:
            # read in until the end
            if current_frame < worker_frame_end:
                amount_load = int(min(batch_size, worker_frame_end - current_frame))
                with lock_video_capture:
                    buffer += [video_capture.read() for i in
                               range(0, amount_load)]
                current_frame += amount_load
                need_more_frame = False
            else:
                # no more frame
                break

        # purge buffer until we find a possible list
        while True:
            if len(buffer) == 0:
                need_more_frame = True
                break
            if frame_acceptance_ctype[int(buffer[0].position_frame - frame_start)]:
                worker_last_candidate = buffer[0]
                break
            else:
                buffer.popleft()

        if need_more_frame:
            continue

        # greedy
        iter_buffer = iter(buffer)
        frame_initial = next(iter_buffer)  # type: CVFrame
        frame_initial_gray = frame_initial.get_cv_mat_grayscale(gray_scale_conversion_code)
        previous_frame_gray = frame_initial_gray.copy()
        previous_frame_features = cv2.goodFeaturesToTrack(previous_frame_gray,
                                                          mask=None,
                                                          **feature_params)

        integral_mean_distance = 0
        frame_candidate = None
        frame_candidate_distance = None
        frame_last_candidate = frame_initial
        frame_last_candidate_distance = 0
        for frame_i in iter_buffer:  # type: CVFrame
            frame_i_gray = frame_i.get_cv_mat_grayscale(
                gray_scale_conversion_code)
            frame_i_features, feature_status, err = \
                cv2.calcOpticalFlowPyrLK(previous_frame_gray, frame_i_gray,
                                         previous_frame_features,
                                         None,
                                         **lucas_kanade_params)

            num_features_left = feature_status.sum()

            if num_features_left == 0:
                # we are lost
                # set the last accept frame to get maximum distance
                frame_candidate = frame_last_candidate
                break

            good_previous_features = previous_frame_features[
                feature_status == 1]
            good_i_features = frame_i_features[feature_status == 1]

            immediate_displacement = (good_i_features - good_previous_features) ** 2
            immediate_distance = np.sqrt(np.sum(immediate_displacement, axis=1))
            mean_immediate_distance = stats.trimboth(immediate_distance,
                                                     0.1).mean()
            integral_mean_distance += mean_immediate_distance

            # print('optical flow process [%d] matching %d[%d] -> %d[%d], int distance '
            #      '= %d' %
            #      (os.getpid(),
            #       int(frame_initial.position_frame),
            #       frame_acceptance_ctype[int(frame_initial.position_frame - frame_start)],
            #       int(frame_i.position_frame),
            #       frame_acceptance_ctype[int(frame_i.position_frame - frame_start)],
            #       integral_mean_distance))

            if frame_acceptance_ctype[int(frame_i.position_frame - frame_start)]:
                # we need to maintain the last accepted one as candidate
                # and the corresponding skip count till that candidate
                # skipped_frame_count += int(frame_i.position_frame - frame_last_candidate.position_frame)
                frame_last_candidate = frame_i
                frame_last_candidate_distance = integral_mean_distance

            previous_frame_gray = frame_i_gray.copy()
            previous_frame_features = good_i_features.reshape(-1, 1, 2)

            if integral_mean_distance < distance_limit:
                continue

            if not frame_acceptance_ctype[int(frame_i.position_frame - frame_start)]:
                # only select accepted ones as candidate
                frame_candidate = frame_last_candidate
                frame_candidate_distance = frame_last_candidate_distance
            else:
                frame_candidate = frame_i
                frame_candidate_distance = integral_mean_distance
            break

        # found the frame?
        if frame_candidate is None:
            need_more_frame = True
            continue

        worker_last_candidate = frame_candidate
        skipped_count = int(frame_candidate.position_frame - frame_initial.position_frame)

        # matched
        # logging.info('proc [%d] matched %d -> %d' %
        #              (os.getpid(), int(template.position_frame), int(image.position_frame)))
        # print('optical flow process [%d] matched %d -> %d, skipped %d, int distance = %d' %
        #       (os.getpid(), int(frame_initial.position_frame),
        #        int(frame_candidate.position_frame),
        #        skipped_count,
        #        frame_candidate_distance))

        # we don't want to reject the initial frame
        buffer.popleft()
        # remove unmatched
        for i in range(0, skipped_count-1):
            f = buffer.popleft()  # type: CVFrame
            # special handling for greedy algorithm
            if (f.position_frame < worker_frame_start + skip_window_both_end) or \
                    (f.position_frame > worker_frame_end - skip_window_both_end):
                # skip first and last frame_rate frames on each worker
                continue
            frame_acceptance_ctype[int(f.position_frame) - frame_start] = False

        with progress_value.get_lock():
            progress_value.value += (skipped_count + 1) / frame_count

    # purge the last bit of the acceptance array
    print('last candidate %d' % worker_last_candidate.position_frame)
    for i in range(int(worker_last_candidate.position_frame+1),
                   worker_frame_end - skip_window_both_end):
        frame_acceptance_ctype[i - frame_start] = False

    with lock_video_capture:
        video_capture.release()


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

        skip_window_both_end = int(cv_video_capture.get_frame_rate())
        # worker_count = 1
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
                      gray_scale_conversion_code,
                      skip_window_both_end
                      )
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
                          gray_scale_conversion_code,
                          skip_window_both_end
                          ))

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

        final_pass_ranges = generate_multiprocessing_final_pass_ranges \
            (frame_acceptance_ctype, frame_count, task_per_worker, worker_count, skip_window_both_end)

        final_pass_arg_list = [(range_i[0], range_i[1],
                                frame_start, frame_count, batch_size,
                                distance_limit,
                                self.feature_params,
                                self.lucas_kanade_params,
                                frame_acceptance_ctype,
                                cv_video_capture.file_handle,
                                progress_value,
                                lock_video_capture,
                                gray_scale_conversion_code)
                               for range_i in final_pass_ranges]

        final_pass_processes = [Process(target=_test_optical_flow_capture_worker,
                                        args=arg_tuple) for arg_tuple in final_pass_arg_list]

        def update_progress_tracker_final_pass():
            progress_tracker.progress = 0.7 + progress_value.value * 0.3

        progress_value.value = 0
        if progress_tracker:
            progress_timer.function = update_progress_tracker_final_pass

        for p in final_pass_processes:
            p.start()
        for p in final_pass_processes:
            p.join()

        if progress_tracker:
            progress_timer.cancel()
            progress_tracker.complete()

        return np.array(frame_acceptance_ctype, dtype=np.bool_).copy()
        pass
