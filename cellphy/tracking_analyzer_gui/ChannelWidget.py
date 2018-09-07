from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, \
    QSpinBox, QDoubleSpinBox, QHBoxLayout, QGroupBox, QPushButton, QToolBar, QAction, QMainWindow, QFrame
import PyQt5.QtCore as QtCore
from cellphy.Analysis.Track import Track
from cellphy.Analysis.Channel import Channel


class ChannelWidget(QMainWindow):
    track_clicked = QtCore.pyqtSignal(Track)
    display_msd_channel = QtCore.pyqtSignal(Channel)

    def __init__(self, channel, parent=None):
        QMainWindow.__init__(self, parent)
        self.listWidget = QListWidget()
        self.channel = channel

        self.tool_bar = ToolBarWidget(self)

        self.tool_bar.button_clicked.connect(self.__msd_channel)
        for _id in self.channel.track_ids:
            list_item = QListWidgetItem()
            _track = self.channel.get_track(float(_id))
            list_item.setText(f'{_id} - ({len(_track.time_position_map)})')
            list_item.setData(QtCore.Qt.UserRole+1, f'{_id}')
            self.listWidget.addItem(list_item)

        self.listWidget.itemClicked.connect(self.__track_clicked)

        self.addToolBar(self.tool_bar)
        self.setCentralWidget(self.listWidget)

    def __track_clicked(self, item):
        track_id = item.data(QtCore.Qt.UserRole+1)
        _track = self.channel.get_track(float(track_id))

        self.track_clicked.emit(_track)

    def __msd_channel(self):
        self.display_msd_channel.emit(self.channel)


class ToolBarWidget(QToolBar):
    spin_change = QtCore.pyqtSignal(float)
    button_clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QToolBar.__init__(self, parent)

        self._frame = QFrame()
        self._frame.setFrameShape(QFrame.StyledPanel)
        self._frame.setFrameShadow(QFrame.Plain)
        self._layout = QHBoxLayout(self._frame)

        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(0)
        self.spin_box.setSingleStep(1)

        self.spin_btn = QPushButton('Bin, MSD and Fit')
        self.spin_btn.clicked.connect(self.spin_btn_clicked)

        self._layout.addWidget(self.spin_box)
        self._layout.addWidget(self.spin_btn)
        self.addSeparator()
        self._frame.setLayout(self._layout)

        self.btn = QPushButton('MSD')
        self.btn.clicked.connect(self.button_clicked)

        self.addWidget(self._frame)
        self.addSeparator()
        self.addWidget(self.btn)

    def set_spin(self, value):
        self.spin_box.setValue(value)

    def spin_value(self):
        return self.spin_box.value()

    def spin_btn_clicked(self):
        self.spin_btn.setEnabled(False)
        self.spin_box.setEnabled(False)
        self.spin_change.emit(self.spin_box.value())

    def enable_spin_btn(self):
        self.spin_box.setEnabled(True)
        self.spin_btn.setEnabled(True)

