from collections import deque

import cv2

from cvutils import CVFrame, CVVideoCapture


def _calculate_correlation_cvmat(cvmat_grayscale, template_grayscale):
    result = cv2.matchTemplate(cvmat_grayscale, template_grayscale,
                               cv2.TM_CCORR_NORMED)
    return result[0][0]


def _calculate_correlation_capture_worker(worker_frame_start,
                                          worker_frame_end,
                                          frame_count,
                                          batch_size,
                                          correlation_limit,
                                          worker_frame_acceptance_ctype,
                                          file_handle,
                                          progress_value,
                                          lock_video_capture,
                                          gray_scale_conversion_code):
    video_capture = CVVideoCapture(file_handle)
    frame_rate = video_capture.get_frame_rate()
    total_frame = worker_frame_end - worker_frame_start
    done = False
    buffer = deque()
    current_frame = worker_frame_start
    while not done:

        # read in until the end
        if current_frame < worker_frame_end:
            amount_load = int(min(batch_size, worker_frame_end - current_frame))
            buffer += [video_capture.read() for i in range(0, amount_load)]
            current_frame += amount_load

        # purge
        while True:
            if worker_frame_acceptance_ctype[int(buffer[0].position_frame)]:
                break
            else:
                buffer.popleft()

        pass
        # if total_frame > batch_size:
        #     with lock_video_capture:
        #         video_capture.set_position_frame(worker_frame_start)
        #         frame_list = [video_capture.read() for i in range(0, batch_size)]
        #         worker_frame_start += batch_size
        #     total_frame -= batch_size
        # else:
        #     with lock_video_capture:
        #         video_capture.set_position_frame(worker_frame_start)
        #         frame_list = [video_capture.read() for i in range(0, total_frame)]
        #     total_frame = 0
        # for frame in frame_list:
        #     pass
            # frame_sharpness_ctype[int(frame.position_frame)] = \
            #     _calculate_sharpness_cvmat(
            #         frame.get_cv_mat_grayscale(gray_scale_conversion_code),
            #         kernel_x, kernel_y)
        # with progress_value.get_lock():
        #     progress_value.value += len(frame_list) / frame_count
    pass


class CVCorrelation:
    def __init__(self):
        pass

    @staticmethod
    def calculate_correlation_frame(cv_frame: CVFrame,
                                    cv_frame_template: CVFrame,
                                    gray_scale_conversion_code=cv2.COLOR_BGR2GRAY):
        return _calculate_correlation_cvmat(
            cv_frame.get_cv_mat_grayscale(gray_scale_conversion_code),
            cv_frame_template.get_cv_mat_grayscale(gray_scale_conversion_code),
        )
