import sys
from .MainWindow import MainWindow
from PyQt5.QtWidgets import QApplication


def start_ui(args):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setMinimumSize(1204, 800)
    window.show()
    sys.exit(app.exec_())

