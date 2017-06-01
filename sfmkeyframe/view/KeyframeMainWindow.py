import os

from PyQt5 import QtCore

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox

from cvutils import CVVideoCapture
from sfmkeyframe.view.ui.KeyframeMainWindow import Ui_KeyframeMainWindow


class KeyframeMainWindow(QMainWindow):
    def __init__(self):
        super(KeyframeMainWindow, self).__init__()
        self.ui = Ui_KeyframeMainWindow()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.ui.pushButton_load.clicked.connect(self.pushButton_load_clicked)
        self.cv_video_cap = None  # type: CVVideoCapture

    def show_error(self, error):
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle('Error')
        msgbox.setIcon(QMessageBox.Warning)
        msgbox.setText(error)
        msgbox.show()

    def pushButton_load_clicked(self):
        if self.cv_video_cap:
            self.cv_video_cap.release()
        filename = QFileDialog.getOpenFileName(self, 'Open video file',
                                               os.path.dirname(os.getcwd()),
                                               )[0]
        if not os.path.exists(filename):
            return self.show_error('File does not exists')
        self.cv_video_cap = CVVideoCapture(filename)
        if not self.cv_video_cap.is_open:
            return self.show_error('Unable to open file\n%s' % filename)
        else:
            print('Video file loaded %s' % filename)

    def closeEvent(self, e):
        super(KeyframeMainWindow, self).closeEvent(e)
