from PyQt5 import QtCore

import cv2
from PyQt5.QtGui import QImage


class CVFrame:
    def __init__(self, cv_mat, grayscale=False, abs_scale_conversion=False):
        self.abs_scale_conversion = abs_scale_conversion
        self.grayscale = grayscale
        self._cv_mat = cv_mat
        self.image = None
        self.height, self.width = cv_mat.shape[:2]

    @property
    def cv_mat(self):
        return self._cv_mat

    @cv_mat.setter
    def cv_mat(self, mat):
        self._cv_mat = mat
        self.image = None
        self.height, self.width = self._cv_mat.shape[:2]

    def get_image(self, scaled_width=None, scaled_height=None):
        if self.image:
            return self.image
        cv_mat = self._cv_mat
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
        if scaled_width and scaled_height:
            return self.image.scaled(scaled_width, scaled_height,
                                     QtCore.Qt.KeepAspectRatio)
        return self.image

