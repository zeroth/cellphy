import PyQt5.QtCore as QtCore

from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, \
    QFileDialog, QStatusBar, QDockWidget, QTextEdit, QMessageBox, QSplitter, QSpinBox

from .CentralWdiget import CentralWidget
from .AnalyzerWrapper import AnalyzerWrapper
from .VTKWidget import VTKWidget
from .MsdChartWidget import MSDWidget
from .IEDWidget import IEDWidget
from .AlfaTotalTable import AlfaTotalTable


class MainWindow(QMainWindow):
    apply_filter = QtCore.pyqtSignal(int)
    bin_updated = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.tool_bar = self.addToolBar('Main Toolbar')
        self.central_widget = CentralWidget(self)
        self.setCentralWidget(self.central_widget)
        self.min_time_points = 4
        self.bin_box = QSpinBox()
        self.filter_box = QSpinBox()
        self.update_toolbar()
        # output window
        self.output_widget = QTextEdit()
        self.output_widget.setReadOnly(True)
        b_dock = QDockWidget('Output')
        b_dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        b_dock.setWidget(self.output_widget)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, b_dock)
        self.tool_bar.addAction(b_dock.toggleViewAction())

        # Analyzer container tab widget
        self.analyzer_container = QTabWidget(self)
        self.analyzer_container.setTabPosition(QTabWidget.West)
        self.analyzer_container.setMovable(True)
        l_dock = QDockWidget('Analyzer container')
        l_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        l_dock.setWidget(self.analyzer_container)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, l_dock)
        self.tool_bar.addAction(l_dock.toggleViewAction())

        # status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

    @QtCore.pyqtSlot(str)
    def print(self, text=''):
        if type(text) is not 'str':
            text = text.__str__()

        self.output_widget.insertPlainText(text)
        self.output_widget.repaint()

    def update_toolbar(self):
        open_files_act = QAction("&Open Channels", self)
        open_files_act.setShortcut(QtCore.Qt.CTRL+QtCore.Qt.Key_O)
        open_files_act.triggered.connect(self.init_analyzer)
        self.tool_bar.addAction(open_files_act)

        tile_act = QAction('&Tile Windows', self)
        tile_act.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_T)
        tile_act.triggered.connect(self.central_widget.tileSubWindows)
        self.tool_bar.addAction(tile_act)

        cls_act = QAction('&Close All Windows', self)
        cls_act.triggered.connect(self.central_widget.closeAllSubWindows)
        self.tool_bar.addAction(cls_act)

        self.filter_box.setPrefix('Min Time')
        self.filter_box.setMinimum(self.min_time_points)
        self.tool_bar.addWidget(self.filter_box)
        flt_action = QAction('Apply Filter', self)
        flt_action.triggered.connect(self.__apply_filter)
        self.tool_bar.addAction(flt_action)

        self.tool_bar.addSeparator()

        self.bin_box.setPrefix('Time Bin')
        self.bin_box.setMinimum(0)
        self.bin_box.valueChanged.connect(self.bin_updated)
        self.tool_bar.addWidget(self.bin_box)

    def __apply_filter(self):
        self.apply_filter.emit(self.filter_box.value())

    def show_warning(self, text):
        msg_box = QMessageBox(self)
        msg_box.setText(text)
        msg_box.exec()

    def init_analyzer(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select channels .csv files",
                                                QtCore.QDir.homePath(), "CSV (*.csv)")

        if not len(files):
            return

        self.print('> loading channels\n')
        analyzer_widget = AnalyzerWrapper(files, self)
        analyzer_widget.statusUpdate.connect(self.print)
        analyzer_widget.track_clicked.connect(self.display_track)
        analyzer_widget.render_all_channels.connect(self.display_all_channels)
        analyzer_widget.render_pair.connect(self.display_pair)
        analyzer_widget.display_msd_tracks.connect(self.display_msd_tracks)
        analyzer_widget.display_channel_msd.connect(self.display_channel)
        analyzer_widget.display_channel_co_traffic.connect(self.display_channel)
        analyzer_widget.display_bin_total.connect(self.display_alfa_table)
        self.apply_filter.connect(analyzer_widget.apply_filter)
        self.bin_updated.connect(analyzer_widget.bin_updated)

        self.analyzer_container.addTab(analyzer_widget, analyzer_widget.title)
        self.print('> done loading channels\n')

    def display_track(self, track):
        window = self.find_mdi_child(track.name)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        chart = MSDWidget(track, track.name)
        chart.setWindowTitle(track.name)
        self.central_widget.add_widget(chart)

    def display_all_channels(self, channels):
        vtk_widget = VTKWidget(self)
        title = ''
        for index, channel in enumerate(channels):
            title += f'{" - " if index > 0 else "" }{channel.name}'

        window = self.find_mdi_child(title)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        for index, channel in enumerate(channels):
            title += f'{" - " if index > 0 else "" }{channel.name}'
            for track in channel.tracks:
                vtk_widget.add_track(track)
            # self.print(track_pos)
        vtk_widget.render_lines()

        vtk_widget.setWindowTitle(title)
        self.central_widget.add_widget(vtk_widget)
        vtk_widget.show()

    def display_pair(self, tracks):
        title = 'pair '
        for index, track in enumerate(tracks):
            title += f'{" - " if index > 0 else "" }{track.name}:{track.track_id}'

        window = self.find_mdi_child(title)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        chart = MSDWidget(tracks, title)
        chart.msd_line_clicked.connect(self.display_track)
        # chart.bar_clicked.connect(vtk_widget.display_points)

        chart.setWindowTitle(title)
        self.central_widget.add_widget(chart)

    def display_msd_tracks(self, tracks, title):
        # vtk_widget = VTKWidget(self)

        window = self.find_mdi_child(title)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        chart = MSDWidget(tracks, title)
        chart.msd_line_clicked.connect(self.display_track)

        chart.setWindowTitle(title)
        self.central_widget.add_widget(chart)

    def display_channel(self, channel, vtk_on=True, show_ied=True, show_alfa=True):
        title = f'{channel.name}-{channel.suffix}-{channel.bin_value}-{channel.filter_size}'

        window = self.find_mdi_child(title)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        splitter = QSplitter(self)

        chart = MSDWidget(channel.tracks, title, vtk_on=vtk_on, show_alfa_table=show_alfa)
        chart.msd_line_clicked.connect(self.display_track)
        # chart.msd_line_clicked.connect(vtk_widget.highlight_track)
        chart.setWindowTitle(f'MSD {title}')

        splitter.addWidget(chart)

        if show_ied:
            ied_widget = IEDWidget(channel)
            splitter.addWidget(ied_widget)
        splitter.setWindowTitle(title)
        self.central_widget.add_widget(splitter)

    def display_alfa_table(self, total_dict, title):
        window = self.find_mdi_child(title)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        alfa_widget = AlfaTotalTable(dictionary=total_dict, title=title)
        self.central_widget.add_widget(alfa_widget)

    def find_mdi_child(self, title):
        for window in self.central_widget.subWindowList():
            if window.windowTitle() == title:
                return window

        return None
