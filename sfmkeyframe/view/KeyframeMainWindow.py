from PyQt5 import QtCore

from PyQt5.QtWidgets import QMainWindow
from sfmkeyframe.view.ui.KeyframeMainWindow import Ui_KeyframeMainWindow


class KeyframeMainWindow(QMainWindow):
    def __init__(self):
        super(KeyframeMainWindow, self).__init__()
        self.ui = Ui_KeyframeMainWindow()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)

    def closeEvent(self, e):
        super(KeyframeMainWindow, self).closeEvent(e)
