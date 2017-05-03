import logging
import multiprocessing
import os
from multiprocessing import RLock, Process

import cv2
import numpy as np

from cvutils import CVVideoCapture, CVAcceptanceTest
from cvutils.cvprogresstracker import CVProgressTracker
from utils import RepeatingTimer, stats
from .cvframe import CVFrame


def _calculate_sharpness_cvmat(cv_mat_grayscale, kernel_x, kernel_y):
    height, width = cv_mat_grayscale.shape[:2]
    filtered_x = cv2.filter2D(cv_mat_grayscale, cv2.CV_64F, kernel_x)
    filtered_y = cv2.filter2D(cv_mat_grayscale, cv2.CV_64F, kernel_y)
    sharpness = (np.sum(filtered_y ** 2) +
                 np.sum(filtered_x ** 2)) / float(height * width * 2)
    return sharpness


def _calculate_sharpness_video_capture_worker(worker_frame_start,
                                              worker_frame_end,
                                              frame_start,
                                              frame_count,
                                              batch_size,
                                              kernel_x, kernel_y,
                                              frame_sharpness_ctype,
                                              file_handle,
                                              progress_value,
                                              lock_video_capture,
                                              gray_scale_conversion_code):
    video_capture = CVVideoCapture(file_handle)
    total_frame = worker_frame_end - worker_frame_start
    while total_frame != 0:
        if total_frame > batch_size:
            with lock_video_capture:
                # logging.info('Process %d - Reading %d frames from '
                #              '%d', os.getpid(), batch_size,
                #              worker_frame_start)
                print('[Sharpness] Process %d - Reading %d frames from '
                      '%d' % (os.getpid(), batch_size, worker_frame_start))
                video_capture.set_position_frame(worker_frame_start)
                frame_list = [video_capture.read() for i in
                              range(0, batch_size)]
                worker_frame_start += batch_size
            total_frame -= batch_size
        else:
            with lock_video_capture:
                # logging.info('Process %d - Reading %d frames from '
                #              '%d, last batch', os.getpid(),
                #              total_frame, worker_frame_start)
                # print('Process %d - Reading %d frames from '
                #       '%d, last batch', os.getpid(),
                #       total_frame, worker_frame_start)
                video_capture.set_position_frame(worker_frame_start)
                frame_list = [video_capture.read() for i in
                              range(0, total_frame)]
            total_frame = 0
        for frame in frame_list:
            frame_sharpness_ctype[int(frame.position_frame - frame_start)] = \
                _calculate_sharpness_cvmat(
                    frame.get_cv_mat_grayscale(gray_scale_conversion_code),
                    kernel_x, kernel_y)
        with progress_value.get_lock():
            progress_value.value += len(frame_list) / frame_count
    video_capture.release()


class CVSharpness(CVAcceptanceTest):
    def __init__(self, use_sobel=False):
        super(CVSharpness, self).__init__('sharpness')
        self.kernel_x = np.array([(0, 0, 0), (-1, 0, 1), (0, 0, 0)], np.double)
        self.kernel_y = np.array([(0, -1, 0), (0, 0, 0), (0, 1, 0)], np.double)
        if use_sobel:
            # sobel will compute gradient with smoothing
            self.kernel_x = np.array([(1, 0, -1), (2, 0, -2), (1, 0, -1)],
                                     np.double)
            self.kernel_y = np.array([(1, 2, 1), (0, 0, 0), (-1, -2, -1)],
                                     np.double)

    def calculate_sharpness_video_capture(self,
                                          cv_video_capture: CVVideoCapture,
                                          frame_start=0, frame_end=None,
                                          batch_size=200,
                                          gray_scale_conversion_code=cv2.COLOR_BGR2GRAY,
                                          progress_tracker:
                                          CVProgressTracker = None):
        frame_count = int(cv_video_capture.get_frame_count())
        if frame_end:
            cv_video_capture.set_position_frame(frame_start)
            frame_count = min(frame_end - frame_start, frame_count)
            frame_count = max(frame_count, 0)

        if progress_tracker:
            progress_tracker.running = True

        frame_sharpness_ctype = multiprocessing.Array('d', frame_count)
        progress_value = multiprocessing.Value('d')
        progress_value.value = 0
        lock_video_capture = RLock()

        worker_count = multiprocessing.cpu_count()
        task_per_worker = int(frame_count / worker_count)
        args_list = [(task_per_worker * i, task_per_worker * (i + 1),
                      frame_start, frame_count, batch_size,
                      self.kernel_x, self.kernel_y,
                      frame_sharpness_ctype,
                      cv_video_capture.file_handle,
                      progress_value,
                      lock_video_capture,
                      gray_scale_conversion_code)
                     for i in range(0, worker_count - 1)]
        args_list.append((task_per_worker * (worker_count - 1), frame_count,
                          frame_start, frame_count, batch_size,
                          self.kernel_x, self.kernel_y,
                          frame_sharpness_ctype,
                          cv_video_capture.file_handle,
                          progress_value,
                          lock_video_capture,
                          gray_scale_conversion_code
                          ))

        processes = [Process(target=_calculate_sharpness_video_capture_worker,
                             args=arg_tuple) for arg_tuple in args_list]

        def update_progress_tracker():
            progress_tracker.progress = progress_value.value

        progress_timer = RepeatingTimer(0.5, update_progress_tracker)

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
            progress_tracker.complete()
        return np.array(frame_sharpness_ctype)

    def calculate_sharpness_frame(self, cv_frame: CVFrame,
                                  gray_scale_conversion_code
                                  =cv2.COLOR_BGR2GRAY):
        if cv_frame is None:
            return 0
        return _calculate_sharpness_cvmat(cv_frame.get_cv_mat_grayscale
                                          (gray_scale_conversion_code),
                                          self.kernel_x, self.kernel_y)

    # @staticmethod
    # def save_calculation_file(sharpness_calculated, cv_video_cap: CVVideoCapture):
    #
    #     np.save(cv_video_cap.file_handle + '.sharpness.' +
    #             str(sharpness_calculated.size) + '.npy', sharpness_calculated)
    #
    # @staticmethod
    # def load_calculation_file(cv_video_cap: CVVideoCapture, count=0):
    #     file_path = cv_video_cap.file_handle + '.sharpness.' + \
    #                 str(cv_video_cap.frame_count if count == 0 else count) + \
    #                 '.npy'
    #     if os.path.exists(file_path):
    #         return np.load(file_path)
    #     return None

    @staticmethod
    def test_sharpness_acceptance(sharpness_calculated: np.ndarray,
                                  frame_window_size, z_score=1.0,
                                  median_absolute_deviation=True,
                                  progress_tracker: CVProgressTracker = None):
        # single sided, only reject if sharpness < (-sigma_bound * \sigma)
        # median absolute deviation ref http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
        frame_window_size = int(round(frame_window_size))
        sigma_bound = abs(z_score)
        result = np.array([], dtype=np.bool_)
        frame_count = sharpness_calculated.shape[0]
        if progress_tracker:
            progress_tracker.running = True
        for i in range(0, frame_count, frame_window_size):
            window = sharpness_calculated[i: i + min(frame_window_size,
                                                     frame_count - i)]  # type: np.ndarray
            result_window = np.ones_like(window, dtype=np.bool_)
            if median_absolute_deviation:
                window_median = np.median(stats.trimboth(window, 0.1))
                diff = window - window_median
                abs_diff = np.abs(diff)
                median_deviation = np.median(abs_diff)
                window_z_score = \
                    (
                    0.6745 * diff) / median_deviation if median_deviation else 0.
                result_window[window_z_score < -sigma_bound] = False
            else:
                window_mean = stats.trimboth(window, 0.1).mean()
                window_std = window.std()
                diff = (window - window_mean)
                result_window[diff < -sigma_bound * window_std] = False
            result = np.concatenate((result, result_window))
            if progress_tracker:
                progress_tracker.progress = i / frame_count
        if progress_tracker:
            progress_tracker.complete()
        return result
