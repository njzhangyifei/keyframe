"""
VideoWidget
    a custom Qt widget for displaying video in Qt environment
    
    Yifei Zhang (c) 2017
"""

from PyQt5 import QtCore, QtGui

from PyQt5.QtCore import QTimer, QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtWidgets import QWidget
from cvutils.cvframe import CVFrame
import cv2
import numpy as np


class VideoWidget(QWidget):
    timerStatusChanged = pyqtSignal([bool])

    def __init__(self, frame_rate=0, parent=None):
        QWidget.__init__(self, parent=parent)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(p)
        self.get_frame_func = None
        self.frame_rate = 0
        self.frame = None
        self.frame_fallback = None
        self.image_out = None
        self.active = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.set_frame_rate(frame_rate)

        self.update()

    def start(self):
        if self.frame_rate != 0:
            self.timer.start(1000.0 / self.frame_rate)
            self.active = True
            self.timerStatusChanged.emit(True)

    def stop(self):
        self.timer.stop()
        self.active = False
        self.timerStatusChanged.emit(False)

    def get_fallback_frame(self):
        fallback_image_mat = np.zeros((self.height(), self.width(), 3),
                                      np.uint8)
        fallback_msg = 'N/A'
        font = cv2.FONT_HERSHEY_COMPLEX
        cv2.putText(fallback_image_mat, fallback_msg,
                    (20, 40), font, 1, (255, 255, 255), 1,
                    cv2.LINE_AA)
        self.frame_fallback = CVFrame(fallback_image_mat)
        return self.frame_fallback

    def set_frame_rate(self, frame_rate):
        self.frame_rate = abs(frame_rate)
        if self.active:
            self.stop()
            self.start()

    def attach_get_frame_func(self, get_frame_func):
        if get_frame_func:
            self.get_frame_func = get_frame_func

    def update_frame(self):
        width = self.width()
        height = self.height()
        if self.get_frame_func:
            rtnval = self.get_frame_func()
            if rtnval and type(rtnval) is CVFrame:
                self.frame = rtnval
        if self.frame:
            self.image_out = self.frame.get_image(width, height)
        else:
            if self.frame_fallback and \
                    (self.frame_fallback.width == width
                     and self.frame_fallback.height == height):
                self.image_out = self.frame_fallback.get_image()
            else:
                self.image_out = self.get_fallback_frame().get_image()
        self.update()

    def paintEvent(self, event):
        width = self.width()
        height = self.height()
        painter = QPainter(self)
        if not self.timer.isActive():
            self.image_out = self.get_fallback_frame().get_image()
        if self.image_out:
            top_left = QPoint((width - self.image_out.width())/ 2,
                              (height - self.image_out.height()) / 2)
            painter.drawImage(top_left, self.image_out)

    def closeEvent(self, event):
        self.stop()
        super(VideoWidget, self).closeEvent(event)

