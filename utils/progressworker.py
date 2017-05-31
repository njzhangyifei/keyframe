from PyQt5.QtCore import pyqtSignal, pyqtSlot

from utils.genericworker import GenericWorker


class ProgressWorker(GenericWorker):
    progress_changed = pyqtSignal([float])
    state_changed = pyqtSignal([str])

    @pyqtSlot()
    def run(self):
        self.function(self.progress_changed, self.state_changed, *self.args, **self.kwargs)
        self.finished.emit()
