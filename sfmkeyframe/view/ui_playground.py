import sys
from PyQt5.QtWidgets import QApplication, QProgressDialog

from sfmkeyframe.view.FilterWidget import FilterWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    filter_widget = FilterWidget()
    filter_widget.show()
    sys.exit(app.exec_())
