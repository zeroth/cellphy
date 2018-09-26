from PyQt5.QtWidgets import QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QDoubleSpinBox, QPushButton, QFrame, \
    QMainWindow, QAction, QToolBar
from PyQt5.QtCore import QThread
from cellphy.Analysis.Channel import Channel
from cellphy.Analysis.Track import Track
import PyQt5.QtCore as QtCore
from pathlib import PurePath
from .ChannelWidget import ChannelWidget
from .CoTrafficWidget import CoTrafficWidget
import pandas as pd
import time
import itertools
from cellphy.Analysis.functions import compare_tracks, compare_all_tracks


class AnalyzerWrapper(QMainWindow):

    statusUpdate = QtCore.pyqtSignal(str)
    track_clicked = QtCore.pyqtSignal(Track)
    render_all_channels = QtCore.pyqtSignal(list)
    render_pair = QtCore.pyqtSignal(list)
    display_msd_tracks = QtCore.pyqtSignal(list, str)
    display_channel_msd = QtCore.pyqtSignal(Channel)

    def __init__(self, files, parent=None):
        QMainWindow.__init__(self, parent)

        # self._layout = QVBoxLayout(self)
        self.parent = parent
        self.tab_widget = QTabWidget()
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabPosition(QTabWidget.East)

        self.files = files
        self.title = ''
        self.channels = []
        self.threads = []
        colors = [[0, 255, 255, 255], [255, 0, 255, 255], [255, 255, 0, 255]]

        for index, file in enumerate(self.files):
            self.parent.print(f'> adding channel {PurePath(file).name}\n')
            self.title += f'{" - " if index > 0 else "" }{PurePath(file).name}'
            channel = Channel(file, color=colors[index], suffix=f'_C{index}')
            self.channels.append(channel)
            channel_widget = ChannelWidget(channel, self)
            channel_widget.track_clicked.connect(self.__track_clicked)
            channel_widget.display_msd_channel.connect(self.__msd_channel)
            self.tab_widget.addTab(channel_widget, channel.name)
            self.parent.print(f'> done adding channel {PurePath(file).name}\n')

        if len(self.channels) > 1:
            self.tool_bar = AnalysisToolWidget()
            self.tool_bar.radius_change.connect(self.compare_tracks)
            self.tool_bar.set_radius(1.0)
            self.tool_bar.display_all_channels.connect(self.__render_all_channels)
            self.addToolBar(self.tool_bar)
        self.setCentralWidget(self.tab_widget)
        self.tab_widget.setCurrentIndex(0)

    def __track_clicked(self, track):
        self.track_clicked.emit(track)

    def __render_all_channels(self):
        self.render_all_channels.emit(self.channels)

    def __display_pair(self, tracks):
        self.render_pair.emit(tracks)

    def __msd_all_tracks(self, tracks, title):
        self.display_msd_tracks.emit(tracks, title)

    def __msd_channel(self, channel):
        self.display_channel_msd.emit(channel)

    def compare_tracks(self, radius):
        thread_pair = CompareThread(self.channels, radius)
        thread_pair.result_ready.connect(self.create_common_co_traffic_widget)
        thread_pair.output.connect(self.parent.print)
        thread_pair.status.connect(self.parent.status_bar.showMessage)
        thread_pair.finished.connect(self.parent.status_bar.currentMessage)
        thread_pair.finished.connect(thread_pair.deleteLater)

        thread_pair.start()
        self.threads.append(thread_pair)

        # thread_all = CompareAllThread(self.channels, radius)
        # thread_all.result_ready.connect(self.create_common_co_traffic_widget)
        # thread_all.output.connect(self.parent.print)
        # thread_all.status.connect(self.parent.status_bar.showMessage)
        # thread_all.finished.connect(self.parent.status_bar.currentMessage)
        # thread_all.finished.connect(thread_all.deleteLater)
        #
        # thread_all.start()
        # self.threads.append(thread_all)

    def create_co_traffic_widgets(self, results, radius):
        for result in results:
            channel_a = result['c_a']
            channel_b = result['c_b']
            pair = result['pair']
            title = f'Radius - {radius} [{channel_a.name} & {channel_b.name}]'
            pair.to_csv(f'./{title}')
            cotraffic_widget = CoTrafficWidget(pair, channel_a, channel_b, title)
            cotraffic_widget.pair_clicked.connect(self.__display_pair)
            cotraffic_widget.msd_clicked.connect(self.__msd_all_tracks)
            self.tab_widget.insertTab(0, cotraffic_widget, cotraffic_widget.title)

        self.tab_widget.setCurrentIndex(0)
        self.tool_bar.enable_analyze_btn()

    def create_common_co_traffic_widget(self, pairs, union, radius):
        print(f'saving common file for radius {radius}')
        for key, _ in pairs.items():
            print(f'>> pair {key}')
        print('saving union')
        union.to_csv('./union_radius.csv')


class CompareThread(QThread):
    print('creating compare thread')
    result_ready = QtCore.pyqtSignal(list, float)
    status = QtCore.pyqtSignal(str)
    output = QtCore.pyqtSignal(str)

    def __init__(self, channels, radius, parent=None):
        QThread.__init__(self, parent)
        self.channels = channels
        self.radius = radius

    def run(self):
        results = []
        start_time = time.time()
        self.output.emit(f'> started processing for Compare thread {self.radius}\n')
        for channel_a, channel_b in itertools.combinations(self.channels, 2):
            rendered_df = pd.DataFrame()
            self.output.emit(f'  > processing channels {channel_a.name} & {channel_b.name}\n')
            for track_a in channel_a.tracks:
                for track_b in channel_b.tracks:
                    self.status.emit(f'> comparing track {track_a.track_id} - {track_b.track_id}')
                    rendered_df = rendered_df.append(compare_tracks(track_a, track_b, channel_a.suffix,
                                                                    channel_b.suffix, self.radius))
            if not rendered_df.empty:
                results.append({'pair': rendered_df.copy(), 'c_a': channel_a, 'c_b': channel_b})
        self.output.emit(f'> done processing (pair thread) for radius : {self.radius} in {time.time() - start_time}\n')
        self.result_ready.emit(results, self.radius)


class CompareAllThread(QThread):
    result_ready = QtCore.pyqtSignal(pd.DataFrame, pd.DataFrame, float)
    status = QtCore.pyqtSignal(str)
    output = QtCore.pyqtSignal(str)

    def __init__(self, channels, radius, parent=None):
        QThread.__init__(self, parent)
        self.channels = channels
        self.radius = radius

    def run(self):

        start_time = time.time()
        self.output.emit(f'> started processing (all thread) for {self.radius}\n')
        tracks_tuple = []
        suffixes = []
        results_pairs = {}
        results_all = pd.DataFrame()
        for channel in self.channels:
            tracks_tuple.append(channel.tracks)
            suffixes.append(channel.suffix)
        for tracks in itertools.product(*tracks_tuple):
            pairs, pair_union = compare_all_tracks(tracks, suffixes, self.radius)
            for pair_id, pair in pairs.items():
                if results_pairs.get(pair_id, None) is None:
                    results_pairs[pair_id] = pd.DataFrame()
                results_pairs[pair_id].append(pair)
            results_all.append(pair_union)
            self.status.emit('> comparing track ' + ','.join([t.__str__() for t in tracks]))
        self.output.emit(f'> done processing (all thread) for radius : {self.radius} in {time.time() - start_time}\n')
        self.result_ready.emit(results_pairs, results_all, self.radius)


class AnalysisToolWidget(QToolBar):

    radius_change = QtCore.pyqtSignal(float)
    display_all_channels = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QToolBar.__init__(self, parent)

        self.radius_tool_frame = QFrame()
        self.radius_tool_frame.setFrameShadow(QFrame.Plain)
        self.radius_tool_frame.setFrameShape(QFrame.StyledPanel)
        self.radius_layout = QHBoxLayout(self.radius_tool_frame)

        self.spin_box = QDoubleSpinBox()
        self.spin_box.setMinimum(0)
        self.spin_box.setSingleStep(0.1)

        self.analyse_btn = QPushButton('Analyze')
        self.analyse_btn.clicked.connect(self.analyse_btn_clicked)

        self.radius_layout.addWidget(self.spin_box)
        self.radius_layout.addWidget(self.analyse_btn)
        self.radius_tool_frame.setLayout(self.radius_layout)

        self.display_all_btn = QPushButton('Show all Channels')
        self.display_all_btn.clicked.connect(self.display_all_btn_clicked)

        self.addWidget(self.radius_tool_frame)
        self.addSeparator()
        self.addWidget(self.display_all_btn)

    def set_radius(self, value):
        self.spin_box.setValue(value)

    def radius(self):
        return self.spin_box.value()

    def analyse_btn_clicked(self):
        self.analyse_btn.setEnabled(False)
        self.spin_box.setEnabled(False)
        self.radius_change.emit(self.spin_box.value())

    def enable_analyze_btn(self):
        self.spin_box.setEnabled(True)
        self.analyse_btn.setEnabled(True)

    def display_all_btn_clicked(self):
        self.display_all_channels.emit()
