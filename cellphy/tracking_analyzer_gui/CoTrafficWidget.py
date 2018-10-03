from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMainWindow, QAction, QSpinBox
import PyQt5.QtCore as QtCore
from cellphy.Analysis import Track, TrackPair, Channel


class CoTrafficWidget(QMainWindow):
    pair_clicked = QtCore.pyqtSignal(TrackPair)
    msd_clicked = QtCore.pyqtSignal(list, str)
    # Channel, vtk_on, show_ied, show_alfa_table
    show_channel = QtCore.pyqtSignal(Channel, bool, bool, bool)
    show_bin_total = QtCore.pyqtSignal(dict, str)

    def __init__(self, data, radius, title = 'Untitled', parent=None):
        QMainWindow.__init__(self, parent)
        self.list_widget = QListWidget()
        self.data = data
        self.radius = radius
        self.pairs = dict()
        self.title = title
        self.min_time_points = 4
        self.channel_a = None
        self.channel_b = None

        # for pair in self.data:
        #     list_item = QListWidgetItem()
        #     list_item.setText(f'{pair.name} - ({len(pair.time)})')
        #     list_item.setData(QtCore.Qt.UserRole + 1, pair.name)
        #     self.list_widget.addItem(list_item)
        #     self.pairs[pair.name] = pair
        #
        # self.list_widget.itemClicked.connect(self.__track_clicked)
        #
        # self.setCentralWidget(self.list_widget)

        self.tool_bar_top = self.addToolBar('CoTraffic toolbar')
        self.filter_box = QSpinBox()
        self.filter_box.setPrefix('Filter Size')
        self.filter_box.setMinimum(self.min_time_points)
        self.tool_bar_top.addWidget(self.filter_box)
        flt_action = QAction('Apply Filter', self)
        flt_action.triggered.connect(self.__apply_filter)
        self.tool_bar_top.addAction(flt_action)

        self.tool_bar_top.addSeparator()
        self.bin_box = QSpinBox()
        self.bin_box.setPrefix('Bin Size')
        self.bin_box.setMinimum(10)
        self.tool_bar_top.addWidget(self.bin_box)

        self.addToolBarBreak(QtCore.Qt.TopToolBarArea)

        self.tool_bar = self.addToolBar('CoTraffic toolbar Buttons')
        msd_action = QAction('Plot MSD', self)
        msd_action.triggered.connect(self.__plot_msd)
        self.tool_bar.addAction(msd_action)

        self.__extract_channels(extract_tracks=False)
        ca_action = QAction(f'Show {self.channel_a.suffix}', self)
        ca_action.triggered.connect(self.__show_ca)
        self.tool_bar.addAction(ca_action)

        cb_action = QAction(f'Show {self.channel_b.suffix}', self)
        cb_action.triggered.connect(self.__show_cb)
        self.tool_bar.addAction(cb_action)

        self.__apply_filter()


        # bin_act = QAction('Apply Bin', self)
        # bin_act.triggered.connect(self.__apply_bin)
    #TODO: after clicking on channel button use the filter value and bin value and produce the results
    # I guess we can skip the VTK widget for this

    def __apply_filter(self):
        self.min_time_points = self.filter_box.value()
        self.list_widget = QListWidget()
        self.pairs = dict()
        for pair in self.data:
            if len(pair.time) >= self.min_time_points:
                list_item = QListWidgetItem()
                list_item.setText(f'{pair.name} - ({len(pair.time)})')
                list_item.setData(QtCore.Qt.UserRole + 1, pair.name)
                self.list_widget.addItem(list_item)
                self.pairs[pair.name] = pair

        self.list_widget.itemClicked.connect(self.__track_clicked)
        self.setCentralWidget(self.list_widget)

    def __show_ca(self):
        self.__extract_channels()
        self.show_channel.emit(self.channel_a, True, False, True)
        bin_value = self.bin_box.value()
        self._display_bin(self.channel_a, bin_value)

    def __show_cb(self):
        self.__extract_channels()
        self.show_channel.emit(self.channel_b, True, False, True)
        bin_value = self.bin_box.value()
        self._display_bin(self.channel_b, bin_value)

    def _display_bin(self, channel, bin_value):
        bin_tracks = channel.bin_tracks(binsize=bin_value)
        total_dict = {}
        for sb, tb in bin_tracks.items():
            _channel = Channel(channel_name=f'{sb-bin_value}-{sb}_{self.radius:.1f}_{channel.suffix}',
                               suffix=channel.suffix, color=channel.base_color)
            _channel.set_track(tb)
            if not total_dict.get(f'{sb-bin_value}-{sb}', False):
                total_dict[f'{sb-bin_value}-{sb}'] = {'total': 0, 'lt': 0, 'gt': 0}

            current = total_dict[f'{sb-bin_value}-{sb}']
            current['total'] = len(tb)
            for t in tb:
                alfa, _ = t.basic_fit()
                if alfa > 1.4:
                    current['gt'] += 1
                else:
                    current['lt'] += 1

            self.show_channel.emit(_channel, False, False, True)
        self.show_bin_total.emit(total_dict, f'{bin_value}-{self.radius:.1f}-{channel.suffix}')

    def _get_tracks_for_meta(self):
        pair_pick = self.data[0]
        return [pair_pick.track_a, pair_pick.track_b]

    def __track_clicked(self, item):
        pair_id = item.data(QtCore.Qt.UserRole+1)
        self.pair_clicked.emit(self.pairs[pair_id])

    def __plot_msd(self):
        tracks = []
        for _, pair in self.pairs.items():
            if len(pair.time) > 3:
                tracks.append(pair.track_a)
                tracks.append(pair.track_b)

        self.msd_clicked.emit(tracks, self.title)

    def __extract_channels(self, extract_tracks = True):
        # get the channel suffix
        tracks = self._get_tracks_for_meta()
        self.channel_a = Channel(channel_name=f'{self.radius:.1f}{tracks[0].suffix}',
                                 suffix=tracks[0].suffix, color=tracks[0].color)

        self.channel_b = Channel(channel_name=f'{self.radius:.1f}{tracks[1].suffix}',
                                 suffix=tracks[1].suffix, color=tracks[1].color)
        if extract_tracks:
            for _, pair in self.pairs.items():
                if pair.track_a.suffix == self.channel_a.suffix:
                    self.channel_a.add_track(pair.track_a)
                    self.channel_b.add_track(pair.track_b)
                else:
                    self.channel_a.add_track(pair.track_b)
                    self.channel_b.add_track(pair.track_a)





