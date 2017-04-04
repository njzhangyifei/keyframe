import cv2
from PyQt5.QtGui import QImage


class CVFrame:
    def __init__(self, cv_mat, grayscale=False, abs_scale_conversion=False):
        self.abs_scale_conversion = abs_scale_conversion
        self.grayscale = grayscale
        self.cv_mat = cv_mat

    # noinspection PyAttributeOutsideInit
    def get_image(self):
        if self.image:
            return self.image
        cv_mat = self.cv_mat
        if self.abs_scale_conversion:
            cv_mat = cv2.convertScaleAbs(cv_mat)
        height, width = cv_mat.shape[:2]
        if self.grayscale:
            image = QImage(cv_mat.data, width, height, QImage.Format_Grayscale8)
        else:
            bytes_per_line = 3 * width
            image = QImage(cv_mat.data, width, height, bytes_per_line,
                           QImage.Format_RGB888)
        self.image = image
        return self.image
