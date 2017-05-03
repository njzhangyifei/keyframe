from collections import deque

import cv2
import logging

import multiprocessing

from multiprocessing import Process

import numpy as np
import os

from cvutils import CVFrame, CVVideoCapture, CVAcceptanceTest
from cvutils.cvmisc import generate_multiprocessing_final_pass_ranges
from cvutils.cvprogresstracker import CVProgressTracker
from utils import RepeatingTimer, first_occurrence_index, last_occurrence_index


def _calculate_correlation_cvmat(cvmat_grayscale, template_grayscale):
    result = cv2.matchTemplate(cvmat_grayscale, template_grayscale,
                               cv2.TM_CCORR_NORMED)
    return result[0][0]

def _test_correlation_capture_worker(worker_frame_start,
                                     worker_frame_end,
                                     frame_start,
                                     frame_count,
                                     batch_size,
                                     correlation_limit,
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
                amount_load = int(
                    min(batch_size, worker_frame_end - current_frame))
                with lock_video_capture:
                    print('[Correlation] Process %d - Reading %d frames from '
                          '%d' % (os.getpid(), batch_size, current_frame))
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
                break
            if frame_acceptance_ctype[int(buffer[0].position_frame - frame_start)]:
                worker_last_candidate = buffer[0]
                break
            else:
                buffer.popleft()

        if need_more_frame:
            continue

        # greedy, find correlation match for first one
        iter_buffer = iter(buffer)
        template = next(iter_buffer)
        template_gray = template.get_cv_mat_grayscale(
            gray_scale_conversion_code)
        frame_final = None
        skipped_frame_count = 0
        for frame_i in iter_buffer:  # type: CVFrame
            if (frame_i.position_frame < worker_frame_start + skip_window_both_end) or \
                    (frame_i.position_frame > worker_frame_end - skip_window_both_end):
                # skip first and last frame_rate frames on each worker
                skipped_frame_count += 1
                continue
            if not frame_acceptance_ctype[int(frame_i.position_frame - frame_start)]:
                # skip rejected ones
                skipped_frame_count += 1
                continue
            frame_i_gray = frame_i.get_cv_mat_grayscale(
                gray_scale_conversion_code)
            corr = _calculate_correlation_cvmat(frame_i_gray, template_gray)
            if corr > correlation_limit:
                skipped_frame_count += 1
                continue
            frame_final = frame_i
            break

        # found the frame
        if frame_final is None:
            need_more_frame = True
            continue
        else:
            worker_last_candidate = frame_final

        # matched
        # logging.info('proc [%d] matched %d -> %d' %
        #              (os.getpid(), int(template.position_frame), int(frame.position_frame)))
        # print('correlation process [%d] matched %d -> %d' %
        #       (os.getpid(),
        #        int(template.position_frame),
        #        int(frame_final.position_frame)))

        # remove unmatched
        buffer.popleft()
        for i in range(0, skipped_frame_count):
            f = buffer.popleft()  # type: CVFrame
            # special handling for greedy algorithm
            if (f.position_frame < worker_frame_start + skip_window_both_end) or \
                    (f.position_frame > worker_frame_end - skip_window_both_end):
                # skip first and last frame_rate frames on each worker
                continue
            frame_acceptance_ctype[int(f.position_frame) - frame_start] = False

        with progress_value.get_lock():
            progress_value.value += (skipped_frame_count + 1) / (worker_frame_end - worker_frame_start)

    # purge the last bit of the acceptance array
    for i in range(int(worker_last_candidate.position_frame+1),
                   worker_frame_end - skip_window_both_end):
        frame_acceptance_ctype[i - frame_start] = False

    with lock_video_capture:
        video_capture.release()


class CVCorrelation(CVAcceptanceTest):
    def __init__(self):
        super(CVCorrelation, self).__init__('correlation')

    @staticmethod
    def test_correlation_video_capture(cv_video_capture: CVVideoCapture,
                                       correlation_limit,
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

        frame_acceptance_ctype = multiprocessing.Array('b',
                                                       frame_acceptance_np.tolist())
        progress_value = multiprocessing.Value('d')
        lock_video_capture = multiprocessing.RLock()

        skip_window_both_end = int(cv_video_capture.get_frame_rate())
        worker_count = multiprocessing.cpu_count()
        task_per_worker = int(frame_count / worker_count)
        args_list = [(task_per_worker * i, task_per_worker * (i + 1),
                      frame_start, frame_count, batch_size,
                      correlation_limit,
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
                          correlation_limit,
                          frame_acceptance_ctype,
                          cv_video_capture.file_handle,
                          progress_value,
                          lock_video_capture,
                          gray_scale_conversion_code,
                          skip_window_both_end
                          ))

        processes = [Process(target=_test_correlation_capture_worker,
                             args=arg_tuple) for arg_tuple in args_list]

        def update_progress_tracker_first_pass():
            progress_tracker.progress = progress_value.value * 0.7

        progress_timer = RepeatingTimer(0.1, update_progress_tracker_first_pass)

        progress_value.value = 0
        if progress_tracker:
            progress_timer.start()

        if progress_tracker:
            progress_tracker.running = True
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        if progress_tracker:
            progress_timer.cancel()

        print('final pass')

        final_pass_ranges = generate_multiprocessing_final_pass_ranges \
            (frame_acceptance_ctype, frame_count, task_per_worker, worker_count, skip_window_both_end)

        final_pass_arg_list = [(range_i[0], range_i[1],
                                frame_start, frame_count, batch_size,
                                correlation_limit,
                                frame_acceptance_ctype,
                                cv_video_capture.file_handle,
                                progress_value,
                                lock_video_capture,
                                gray_scale_conversion_code,
                                )
                               for range_i in final_pass_ranges]

        final_pass_processes = [Process(target=_test_correlation_capture_worker,
                                        args=arg_tuple) for arg_tuple in final_pass_arg_list]

        def update_progress_tracker_final_pass():
            progress_tracker.progress = 0.7 + progress_value.value / worker_count * 0.3

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

    @staticmethod
    def calculate_correlation_frame(cv_frame: CVFrame,
                                    cv_frame_template: CVFrame,
                                    gray_scale_conversion_code=cv2.COLOR_BGR2GRAY):
        return _calculate_correlation_cvmat(
            cv_frame.get_cv_mat_grayscale(gray_scale_conversion_code),
            cv_frame_template.get_cv_mat_grayscale(gray_scale_conversion_code),
        )
