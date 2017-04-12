import cv2
import numpy as np

from cvutils import CVFrame


def _calculate_correlation_cvmat(cvmat_grayscale, template_grayscale):
    result = cv2.matchTemplate(cvmat_grayscale, template_grayscale,
                               cv2.TM_CCORR_NORMED)
    return result[0][0]


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

