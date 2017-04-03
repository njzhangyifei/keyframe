import sys

from PyQt5.QtWidgets import QFileDialog, QApplication


def selectFile():
    dlg = QFileDialog();
    dlg.setFileMode(QFileDialog.AnyFile)
    filename, filter_type = dlg.getOpenFileNames()
    return filename


if __name__ == '__main__':
    app = QApplication(sys.argv)
    print(selectFile())
