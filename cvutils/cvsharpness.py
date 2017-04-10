import multiprocessing
import os
from multiprocessing import RLock, Process
from time import sleep

import cv2
import numpy as np

from cvutils import CVVideoCapture
from cvutils.cvprogresstracker import CVProgressTracker
from utils import RepeatingTimer
from .cvframe import CVFrame


def _calculate_sharpness_cvmat(cv_mat, kernel_x, kernel_y,
                               gray_scale_conversion_code=cv2.COLOR_BGR2GRAY):
    height, width = cv_mat.shape[:2]
    frame_gray = cv2.cvtColor(cv_mat, gray_scale_conversion_code)
    filtered_x = cv2.filter2D(frame_gray, cv2.CV_64F, kernel_x)
    filtered_y = cv2.filter2D(frame_gray, cv2.CV_64F, kernel_y)
    sharpness = (np.sum(filtered_y ** 2) +
                 np.sum(filtered_x ** 2)) / float(height * width * 2)
    return sharpness


def _calculate_sharpness_video_capture_worker(worker_frame_start,
                                              worker_frame_end,
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
                # print('Process %d - Reading %d frames from '
                #       '%d', os.getpid(), batch_size,
                #       worker_frame_start)
                video_capture.set_position_frame(worker_frame_start)
                frame_tuple_list = [
                    (worker_frame_start + i, video_capture.read())
                    for i in range(0, batch_size)]
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
                frame_tuple_list = [
                    (worker_frame_start + i, video_capture.read())
                    for i in range(0, total_frame)]
            total_frame = 0
        for frame_tuple in frame_tuple_list:
            frame_sharpness_ctype[frame_tuple[0]] = \
                _calculate_sharpness_cvmat(frame_tuple[1].cv_mat,
                                           kernel_x, kernel_y,
                                           gray_scale_conversion_code)
        with progress_value.get_lock():
            progress_value.value += len(frame_tuple_list) / frame_count
    video_capture.release()


class CVSharpness:
    def __init__(self, use_sobel=False):
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
                                          gray_scale_conversion_code=cv2.COLOR_BGR2GRAY,
                                          batch_size=100,
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
                      frame_count, batch_size,
                      self.kernel_x, self.kernel_y,
                      frame_sharpness_ctype,
                      cv_video_capture.file_handle,
                      progress_value,
                      lock_video_capture,
                      gray_scale_conversion_code)
                     for i in range(0, worker_count - 1)]
        args_list.append((task_per_worker * (worker_count - 1), frame_count,
                          frame_count, batch_size,
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
        return self.calculate_sharpness_cvmat(cv_frame.cv_mat,
                                              gray_scale_conversion_code)

    def calculate_sharpness_cvmat(self, cv_mat, gray_scale_conversion_code):
        return _calculate_sharpness_cvmat(cv_mat,
                                          self.kernel_x, self.kernel_y,
                                          gray_scale_conversion_code)

    @staticmethod
    def test_sharpness_acceptance(sharpness_calculated: np.ndarray,
                                  frame_window_size, sigma_bound=1.0,
                                  progress_tracker: CVProgressTracker = None):
        # only reject if sharpness < (-sigma_bound * \sigma)
        frame_window_size = round(frame_window_size)
        sigma_bound = abs(sigma_bound)
        result = np.array([])
        frame_count = sharpness_calculated.shape[0]
        if progress_tracker:
            progress_tracker.running = True
        for i in range(0, frame_count, frame_window_size):
            window = sharpness_calculated[i:i + min(frame_window_size,
                                                    frame_count - i)]
            result_window = np.ones_like(window)
            window_mean = sharpness_calculated.mean()
            window_std = sharpness_calculated.std()
            diff = (window - window_mean)
            result_window[diff < -sigma_bound * window_std] = 0
            result = np.concatenate((result, result_window))
            if progress_tracker:
                progress_tracker.progress = i / frame_count
        if progress_tracker:
            progress_tracker.complete()
        return result
