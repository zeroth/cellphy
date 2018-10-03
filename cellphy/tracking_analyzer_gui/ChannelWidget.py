from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QToolBar, QMainWindow
import PyQt5.QtCore as QtCore
from cellphy.Analysis.Track import Track
from cellphy.Analysis.Channel import Channel


class ChannelWidget(QMainWindow):
    track_clicked = QtCore.pyqtSignal(Track)
    display_msd_channel = QtCore.pyqtSignal(Channel)
    # display_ied_channel = QtCore.pyqtSignal(Channel)
    show_bin_total = QtCore.pyqtSignal(dict, str)

    def __init__(self, channel, parent=None):
        QMainWindow.__init__(self, parent)
        self.listWidget = None
        self.channel = channel
        self.bin_value = 0
        self.tool_bar = ToolBarWidget(self)

        self.tool_bar.msd_button_clicked.connect(self.__msd_channel)

        self.addToolBar(self.tool_bar)

        self.apply_filter()

    def populate_items(self):
        self.listWidget = None
        self.listWidget = QListWidget()
        for index, track in enumerate(self.channel.tracks):
            list_item = QListWidgetItem()
            list_item.setText(f'{index} : {track.track_id} - ({len(track.time_position_map)})')
            list_item.setData(QtCore.Qt.UserRole+1, f'{track.track_id}')
            self.listWidget.addItem(list_item)

        self.listWidget.itemClicked.connect(self.__track_clicked)
        self.setCentralWidget(self.listWidget)

    def __track_clicked(self, item):
        track_id = item.data(QtCore.Qt.UserRole+1)
        _track = self.channel.get_track(float(track_id))

        self.track_clicked.emit(_track)

    def __msd_channel(self):
        print(f' before {self.channel.name}-{self.channel.suffix} tracks {len(self.channel.tracks)}')
        _, track_dict = self.channel.bin_tracks(self.bin_value)
        print(f' after tracks {len(self.channel.tracks)}')
        self.display_msd_channel.emit(self.channel)
        self.show_bin_total.emit(track_dict, f'{self.bin_value}-{self.channel.suffix}-{self.bin_value}')

    def apply_filter(self, value=4):
        self.channel.apply_filter(filter_value = value)
        self.populate_items()

    def bin_updated(self, value=0):
        self.bin_value = value

    # def __ied_channel(self):
    #     self.display_ied_channel.emit(self.channel)


class ToolBarWidget(QToolBar):
    msd_button_clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QToolBar.__init__(self, parent)
        self.msd_btn = QPushButton('MSD & IED & Alfa')
        self.msd_btn.clicked.connect(self.msd_button_clicked)
        self.addWidget(self.msd_btn)


