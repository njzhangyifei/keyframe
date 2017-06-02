import logging

import sys
from PyQt5.QtWidgets import QFileDialog, QApplication


def select_file():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    filename, filter_type = dlg.getOpenFileName()
    return filename

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    logging.info('test')

    app = QApplication(sys.argv)


