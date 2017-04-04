#!/usr/bin/python3.5
import sys
from PyQt5 import QtCore

import cv2
import numpy as np
from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QFileDialog, QApplication, QWidget



def selectFile():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    filename, filter_type = dlg.getOpenFileNames()
    return filename


class QImageMat(QImage):
    def __init__(self, cv_mat):
        height, width, channel = cv_mat.shape
        bytes_per_line = 3 * width
        super().__init__(cv_mat.data, width, height, bytes_per_line,
                         QImage.Format_RGB888)


class VideoWidget(QWidget):
    def __init__(self, capture, frame_rate, parent=None):
        QWidget.__init__(self)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.updateFrame)
        self._timer.start(1000.0 / frame_rate)
        self.capture = capture
        retval, frame = capture.read()
        if not retval:
            raise Exception("Error reading video capture")
        frame = self.buildFrame(frame)
        self.image = QImageMat(frame)
        self.setMinimumSize(self.image.width() / 2, self.image.height() / 2)
        # self.setMinimumSize(self.image.width(), self.image.height())
        self.setMaximumSize(self.minimumSize())
        self.update()

    def buildFrame(self, frame):
        height, width = frame.shape[:2]
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_gray_rgb = cv2.cvtColor(frame_gray, cv2.COLOR_GRAY2RGB)

        kernel_x = np.array([(0, 0, 0), (-1, 0, 1), (0, 0, 0)], np.float)
        kernel_y = np.array([(0, -1, 0), (0, 0, 0), (0, 1, 0)], np.float)
        filtered_x = cv2.filter2D(frame_gray, cv2.CV_64F, kernel_x)
        filtered_y = cv2.filter2D(frame_gray, cv2.CV_64F, kernel_y)
        filtered_x_gray = cv2.convertScaleAbs(filtered_x)
        filtered_y_gray = cv2.convertScaleAbs(filtered_y)
        filtered_x_gray_rgb = cv2.cvtColor(filtered_x_gray, cv2.COLOR_GRAY2RGB)
        filtered_y_gray_rgb = cv2.cvtColor(filtered_y_gray, cv2.COLOR_GRAY2RGB)

        sharpness = (np.sum(filtered_y ** 2)
                     + np.sum(filtered_x ** 2)) / float(height * width * 2)

        # sobel_x = cv2.Sobel(frame_gray, cv2.CV_64F, 1, 0)
        # sobel_y = cv2.Sobel(frame_gray, cv2.CV_64F, 0, 1)
        # laplacian = cv2.Laplacian(frame_gray, cv2.CV_64F)
        # laplacian_gray = cv2.convertScaleAbs(laplacian)
        # laplacian_gray_rgb = cv2.cvtColor(laplacian_gray, cv2.COLOR_GRAY2RGB)
        # sobel_x_gray = cv2.convertScaleAbs(sobel_x)
        # sobel_y_gray = cv2.convertScaleAbs(sobel_y)
        # sobel_x_gray_rgb = cv2.cvtColor(sobel_x_gray, cv2.COLOR_GRAY2RGB)
        # sobel_y_gray_rgb = cv2.cvtColor(sobel_y_gray, cv2.COLOR_GRAY2RGB)

        font = cv2.FONT_HERSHEY_COMPLEX
        cv2.putText(frame_gray_rgb, str(self.capture.get(cv2.CAP_PROP_POS_FRAMES)),
                    (0, 40), font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_gray_rgb, str(sharpness), (0, height - 10),
                    font, 1, (255, 255, 255), 1, cv2.LINE_AA)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        combine = np.zeros((height * 2, width * 2, 3), np.uint8)

        # combine 2 images
        combine[:height, :width, :3] = frame_rgb
        combine[:height, width:width * 2, :3] = frame_gray_rgb
        # combine[height:height*2, width:width*2, :3] = sobel_x_gray_rgb
        # combine[height:height*2, :width, :3] = sobel_y_gray_rgb
        combine[height:height * 2, width:width * 2, :3] = filtered_x_gray_rgb
        combine[height:height * 2, :width, :3] = filtered_y_gray_rgb

        return combine

    def paintEvent(self, event):
        painter = QPainter(self)
        image_to_draw = self.image.scaled(self.image.width() / 2,
                                          self.image.height() / 2,
                                          QtCore.Qt.KeepAspectRatio)
        # image_to_draw = self.image
        painter.drawImage(QPoint(0, 0), image_to_draw)

    def closeEvent(self, event):
        self._timer.stop()
        super(VideoWidget, self).closeEvent(event)

    def getFrame(self):
        retval, frame = self.capture.read()
        if retval:
            self.image = QImageMat(self.buildFrame(frame))

    def updateFrame(self):
        self.getFrame()
        self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    filename = selectFile()[0]
    # filename = '/home/yifei/develop/sealab/keyframe/data/GP017728.MP4'
    # filename = 'C://Users//Yifei//unixhome//develop//sealab//keyframe//data' \
    #            '//GP017728.MP4'
    print('Opening ' + filename)
    video_cap = cv2.VideoCapture(filename)
    frame_rate = video_cap.get(cv2.CAP_PROP_FPS)
    print('Frame rate = ' + str(frame_rate))

    widget = VideoWidget(video_cap, frame_rate * 1.5)

    widget.setWindowTitle('PyQt - OpenCV Test')
    widget.show()

    sys.exit(app.exec_())
