from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMainWindow, QAction
import PyQt5.QtCore as QtCore
from cellphy.Analysis.Track import Track


class CoTrafficWidget(QMainWindow):
    pair_clicked = QtCore.pyqtSignal(list)
    msd_clicked = QtCore.pyqtSignal(list, str)

    def __init__(self, data, channel_a, channel_b, title = 'Untitled', parent=None):
        QMainWindow.__init__(self, parent)
        self.list_widget = QListWidget()
        self.data = data
        self.channels = [channel_a, channel_b]
        self.pairs = dict()
        self.title = title
        # we want to just show top pairs
        self.top_pairs = self.data.groupby('top_pair')
        for name, group in self.top_pairs:
            list_item = QListWidgetItem()
            list_item.setText(f'{name} - ({group.index.size})')
            list_item.setData(QtCore.Qt.UserRole+1, name)
            tracks = []
            for channel in self.channels:
                track_df = group[[f'X{channel.suffix}', f'Y{channel.suffix}', f'Z{channel.suffix}',
                                 f'trackid{channel.suffix}', f'time']]
                track_df = track_df.rename(columns={f'X{channel.suffix}': f'X{channel.suffix}',
                                                    f'Y{channel.suffix}': f'Y{channel.suffix}',
                                                    f'Z{channel.suffix}': f'Z{channel.suffix}',
                                                    f'trackid{channel.suffix}': f'trackid{channel.suffix}'})
                track_id = list(track_df[f'trackid{channel.suffix}'])[0]
                tracks.append(Track(track_id=track_id, name=channel.name, color=channel.base_color, raw_data=track_df,
                                    suffix=channel.suffix))
            self.pairs[name] = tracks

            self.list_widget.addItem(list_item)

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
        flatten = lambda l: [item for sublist in l for item in sublist]
        tracks = list(self.pairs.values())
        tracks = flatten(tracks)
        # print(tracks)
        self.msd_clicked.emit(tracks, self.title)
