import multiprocessing
from multiprocessing import Lock, Value, RLock, Process, JoinableQueue
from multiprocessing.pool import Pool

from cvutils import CVVideoCapture
from cvutils.cvprogresstracker import CVProgressTracker
from .cvframe import CVFrame
import numpy as np
import cv2


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

    shared_data = None

    def calculate_sharpness_video_capture(self,
                                          cv_video_capture: CVVideoCapture,
                                          frame_start=0, frame_end=None,
                                          gray_scale_conversion_code=cv2.COLOR_BGR2GRAY,
                                          progress_tracker:
                                          CVProgressTracker = None):
        frame_count = int(cv_video_capture.get_frame_count())
        if frame_end:
            cv_video_capture.set_position_frame(frame_start)
            frame_count = min(frame_end - frame_start, frame_count)
            frame_count = max(frame_count, 0)
        frame_sharpness = np.zeros([frame_count], np.double)

        if progress_tracker:
            progress_tracker.running = True

        lock_video_capture = RLock()
        lock_progress_tracker = RLock()
        batch_size = 100

        worker_count = multiprocessing.cpu_count() - 1
        task_per_worker = int(frame_count / worker_count)
        # processes = [Process(target=calculate_sharpness_worker,
        #                      args=arg_tuple) for arg_tuple in args_list]
        # processes[0].start()
        # processes[0].join()
        # for p in processes:
        #     p.start()
        # for p in processes:
        #     p.join()

        def test_videocapture(num):
            frame = cv_video_capture.read()
            print('id = ' + num +
                  ' frame='+cv_video_capture.get_position_frame())

        

        # i = 0
        # while i < frame_count:
        #     cv_frame = cv_video_capture.read()
        #     frame_sharpness[i] = \
        #         self.calculate_sharpness_frame(cv_frame,
        #                                        gray_scale_conversion_code)
        #     i += 1
        #     if progress_tracker:
        #         progress_tracker.progress = i / frame_count

        if progress_tracker:
            progress_tracker.complete()
        return frame_sharpness

    def calculate_sharpness_frame(self, cv_frame: CVFrame,
                                  gray_scale_conversion_code
                                  =cv2.COLOR_BGR2GRAY):
        if cv_frame is None:
            return 0
        return self.calculate_sharpness_cvmat(cv_frame.cv_mat,
                                              gray_scale_conversion_code)

    def calculate_sharpness_cvmat(self, cv_mat,
                                  gray_scale_conversion_code
                                  =cv2.COLOR_BGR2GRAY):
        height, width = cv_mat.shape[:2]
        frame_gray = cv2.cvtColor(cv_mat, gray_scale_conversion_code)
        filtered_x = cv2.filter2D(frame_gray, cv2.CV_64F, self.kernel_x)
        filtered_y = cv2.filter2D(frame_gray, cv2.CV_64F, self.kernel_y)
        sharpness = (np.sum(filtered_y ** 2) +
                     np.sum(filtered_x ** 2)) / float(height * width * 2)
        return sharpness

    @staticmethod
    def test_sharpness_acceptance(sharpness_calculated: np.ndarray,
                                  frame_window_size, sigma_bound=1.0,
                                  progress_tracker: CVProgressTracker = None):
        # only reject if sharpness < (-sigma_bound * \sigma)
        frame_window_size = round(frame_window_size)
        sigma_bound = abs(sigma_bound)
        result = np.array([0])
        frame_count = sharpness_calculated.shape[0]
        if progress_tracker:
            progress_tracker.running = True
        for i in range(0, frame_count, frame_window_size):
            window = sharpness_calculated[i:i + frame_window_size]
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
