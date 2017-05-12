import sys
from PyQt5.QtWidgets import QApplication, QProgressDialog

from cvutils import CVVideoCapture
from sfmkeyframe.view.FilterWidget import FilterWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    filename = '/home/yifei/develop/sealab/keyframe/data/GOPR7728.MP4'
    video_cap = CVVideoCapture(filename)
    filter_widget = FilterWidget(video_cap)
    filter_widget.show()
    sys.exit(app.exec_())
