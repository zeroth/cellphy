from PyQt5.QtWidgets import QWidget, QGridLayout, QScrollArea, QMdiArea
import PyQt5.QtCore as QtCore


class ScrollArea(QScrollArea):
    size_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QScrollArea.__init__(self, parent)

    def wheelEvent(self, ev):
        if ev.type() == QtCore.QEvent.Wheel:
            ev.ignore()

    def resizeEvent(self, a0):
        self.size_changed.emit()
        QScrollArea.resizeEvent(self, a0)


class CentralWidget(QMdiArea):
    def __init__(self, parent=None):
        QMdiArea.__init__(self, parent)
        # self.layout = QGridLayout()
        # self.setLayout(self.layout)
        # self.size_changed.connect(self.layout.update)

    def add_widget(self, widget):
        # assert row < 0, "provide a valid row argument"
        # assert col < 0, "provide a valid col argument"
        self.addSubWindow(widget)
        widget.show()
