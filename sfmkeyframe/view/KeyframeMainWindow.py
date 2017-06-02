import os
import webbrowser

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox

from cvutils import CVVideoCapture
from sfmkeyframe.view.FilterWidget import FilterWidget
from sfmkeyframe.view.ui.KeyframeMainWindow import Ui_KeyframeMainWindow


class KeyframeMainWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super(KeyframeMainWindow, self).__init__()
        self.ui = Ui_KeyframeMainWindow()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.ui.pushButton_load.clicked.connect(self.pushButton_load_clicked)
        self.ui.pushButton_help.clicked.connect(self.pushButton_help_clicked)
        self.ui.pushButton_exit.clicked.connect(self.close)
        self.ui.closeEvent = self.closeEvent
        self.opened_videos = {}
        
    def show_error(self, error):
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle('Error')
        msgbox.setIcon(QMessageBox.Warning)
        msgbox.setText(error)
        msgbox.show()

    def filter_widget_closed(self, key):
        print('filter for video file %s is closed' % key)
        cv_video_cap, widget = self.opened_videos[key]
        cv_video_cap.release()
        widget.closed.disconnect(self.filter_widget_closed)
        del self.opened_videos[key]

    def pushButton_help_clicked(self):
        webbrowser.open_new('https://github.com/njzhangyifei/keyframe')

    def pushButton_load_clicked(self):
        filename = QFileDialog.getOpenFileName(self, 'Open video file',
                                               os.path.dirname(os.getcwd()),
                                               )[0] # type: str
        if not filename:
            return
        if not os.path.exists(filename):
            return self.show_error('File does not exists')
        if filename in self.opened_videos:
            print('Video file %s -> already loaded' % filename)
            widget = self.opened_videos[filename][1]  # type: FilterWidget
            if widget.windowState() == QtCore.Qt.WindowMinimized:
                widget.setWindowState(QtCore.Qt.WindowNoState)
            widget.show()
            widget.activateWindow()
            widget.raise_()
            return
        cv_video_cap = CVVideoCapture(filename)
        if not cv_video_cap.is_open:
            return self.show_error('Unable to open file\n%s' % filename)
        else:
            print('Video file %s loaded -> new widget' % filename)
            widget = FilterWidget(cv_video_cap)
            self.opened_videos[filename] = (cv_video_cap, widget)
            widget.closed.connect(self.filter_widget_closed)
            self.closed.connect(widget.close)
            widget.show()

    def closeEvent(self, e):
        if len(self.opened_videos) > 0:
            msg = "Are you really sure you want to exit?\nThere are still opened filter windows."
            reply = QMessageBox.question(self, 'One sec...', msg,
                                         QMessageBox.Yes, QMessageBox.No)
            if reply != QMessageBox.Yes:
                e.ignore()
                return
        self.closed.emit()
        super(KeyframeMainWindow, self).closeEvent(e)
