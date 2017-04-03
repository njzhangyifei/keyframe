import sys
import cv2
from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QFileDialog, QApplication, QWidget


def selectFile():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    filename, filter_type = dlg.getOpenFileNames()
    return filename


class QImageMat(QImage):
    def __init__(self, cv_mat, greyscale=False):
        if greyscale:
            cv_mat = cv2.cvtColor(cv_mat, cv2.COLOR_GRAY2RGB)
        else:
            cv_mat = cv2.cvtColor(cv_mat, cv2.COLOR_BGR2RGB)
        height, width, channel = cv_mat.shape
        bytesPerLine = 3 * width
        super().__init__(cv_mat.data, width, height, bytesPerLine,
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
        self.image = QImageMat(frame)
        self.setMinimumSize(self.image.width(), self.image.height())
        self.setMaximumSize(self.minimumSize())
        self.update()

    def buildFrame(self, frame):
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(frame_gray, cv2.CV_8U)
        return laplacian

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(QPoint(0, 0), self.image)

    def closeEvent(self, event):
        self._timer.stop()
        super(VideoWidget, self).closeEvent(event)

    def getFrame(self):
        retval, frame = self.capture.read()
        if retval:
            self.image = QImageMat(self.buildFrame(frame), True)

    def updateFrame(self):
        self.getFrame()
        self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # filename = selectFile()[0]
    filename = '/home/yifei/develop/sealab/keyframe/data/GP017728.MP4'
    print('Opening ' + filename)
    video_cap = cv2.VideoCapture(filename)
    frame_rate = video_cap.get(cv2.CAP_PROP_FPS)
    print('Frame rate = ' + str(frame_rate))

    widget = VideoWidget(video_cap, frame_rate * 2)

    widget.setWindowTitle('PyQt - OpenCV Test')
    widget.show()

    sys.exit(app.exec_())
