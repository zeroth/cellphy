from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMainWindow, QAction
import PyQt5.QtCore as QtCore
from cellphy.Analysis import Track, TrackPair


class CoTrafficWidget(QMainWindow):
    pair_clicked = QtCore.pyqtSignal(TrackPair)
    msd_clicked = QtCore.pyqtSignal(list, str)

    def __init__(self, data, channel_a, channel_b, title = 'Untitled', parent=None):
        QMainWindow.__init__(self, parent)
        self.list_widget = QListWidget()
        self.data = data
        self.channels = [channel_a, channel_b]
        self.pairs = dict()
        self.title = title
        # we want to just show top pairs
        # self.top_pairs = self.data.groupby('top_pair')
        for pair in self.data:
            list_item = QListWidgetItem()
            list_item.setText(f'{pair.name} - ({len(pair.time)})')
            list_item.setData(QtCore.Qt.UserRole + 1, pair.name)
            self.list_widget.addItem(list_item)
            self.pairs[pair.name] = pair

        self.list_widget.itemClicked.connect(self.__track_clicked)

        self.setCentralWidget(self.list_widget)

        self.tool_bar = self.addToolBar('CoTraffic toolbar')
        msd_action = QAction('Plot MSD', self)
        msd_action.triggered.connect(self.__plot_msd)
        self.tool_bar.addAction(msd_action)

    def __track_clicked(self, item):
        pair_id = item.data(QtCore.Qt.UserRole+1)
        self.pair_clicked.emit(self.pairs[pair_id])

    def __plot_msd(self):
        tracks = []
        for _, pair in self.pairs.items():
            tracks.append(pair.track_a)
            tracks.append(pair.track_b)

        self.msd_clicked.emit(tracks, self.title)
