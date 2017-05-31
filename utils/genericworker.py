from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot


class GenericWorker(QtCore.QObject):

    start = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, func, *args, **kwargs):
        super(GenericWorker, self).__init__()
        self.function = func
        self.args = args
        self.kwargs = kwargs
        self.start.connect(self.run)

    @pyqtSlot()
    def run(self):
        self.function(*self.args, **self.kwargs)
        self.finished.emit()