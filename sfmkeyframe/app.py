import multiprocessing
import sys
from PyQt5.QtWidgets import QApplication
from sfmkeyframe.view.KeyframeMainWindow import KeyframeMainWindow

# for windows compatibility
multiprocessing.set_start_method('spawn')
app = QApplication(sys.argv)

mainWindow = KeyframeMainWindow()
mainWindow.show()

sys.exit(app.exec_())
