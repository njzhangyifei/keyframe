import sys
import threading

import time

import multiprocessing
from PyQt5.QtCore import QObject, pyqtSignal, QThread, Qt
from PyQt5.QtWidgets import QApplication, QProgressDialog

from cvutils import CVVideoCapture
from sfmkeyframe.view.FilterWidget import FilterWidget
from utils.genericworker import GenericWorker

# class t:
#     def __init__(self):
#         self.t = None
#
#     def oooo(self, t, s):
#         self.t = 100
#         for i in range(10):
#             time.sleep(1)
#             print('ttt %d %s' % (t, s))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # obj = GenericWorker(ob.oooo, t=10, s='test')
    # t = QProgressDialog('                    Analysing Video for Image Sharpness                    ', None, 0, 1000)
    # t.setWindowModality(Qt.WindowModal)
    # t.setValue(512)

    # obj.moveToThread(objThread)
    # obj.finished.connect(objThread.quit)
    # objThread.started.connect(obj.run)
    # objThread.start()


    multiprocessing.set_start_method('spawn')
    # filename = 'C:/Users/Yifei/unixhome/develop/sealab/keyframe/data/GP017728.MP4'
    filename = 'C:/Users/Yifei/unixhome/develop/sealab/keyframe/data/test_50s.mp4'
    # filename = '/home/yifei/develop/sealab/keyframe/data/GOPR7728.MP4'
    video_cap = CVVideoCapture(filename)
    filter_widget = FilterWidget(video_cap)
    filter_widget.show()

    sys.exit(app.exec_())
