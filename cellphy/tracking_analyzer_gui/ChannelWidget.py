from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QToolBar, QMainWindow
import PyQt5.QtCore as QtCore
from cellphy.Analysis.Track import Track
from cellphy.Analysis.Channel import Channel


class ChannelWidget(QMainWindow):
    track_clicked = QtCore.pyqtSignal(Track)
    display_msd_channel = QtCore.pyqtSignal(Channel)
    # display_ied_channel = QtCore.pyqtSignal(Channel)

    def __init__(self, channel, parent=None):
        QMainWindow.__init__(self, parent)
        self.listWidget = QListWidget()
        self.channel = channel

        self.tool_bar = ToolBarWidget(self)

        self.tool_bar.msd_button_clicked.connect(self.__msd_channel)
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

    # def __ied_channel(self):
    #     self.display_ied_channel.emit(self.channel)


class ToolBarWidget(QToolBar):
    msd_button_clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QToolBar.__init__(self, parent)
        self.msd_btn = QPushButton('Display')
        self.msd_btn.clicked.connect(self.msd_button_clicked)
        self.addWidget(self.msd_btn)


