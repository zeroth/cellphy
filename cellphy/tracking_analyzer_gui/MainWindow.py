import PyQt5.QtCore as QtCore

from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, \
    QFileDialog, QStatusBar, QDockWidget, QTextEdit, QMessageBox, QSplitter
from PyQt5.QtGui import QTextDocumentWriter, QTextDocument


from .CentralWdiget import CentralWidget
from .AnalyzerWrapper import AnalyzerWrapper
from .VTKWidget import VTKWidget
from .JumpChartWidget import JumpChartWidget
from .MsdChartWidget import MsdChartWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.tool_bar = self.addToolBar('Main Toolbar')
        self.update_toolbar()
        self.central_widget = CentralWidget(self)
        self.setCentralWidget(self.central_widget)

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
        self.analyzer_container.addTab(analyzer_widget, analyzer_widget.title)
        self.print('> done loading channels\n')

    def display_track(self, track):
        window = self.find_mdi_child(track.name)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        splitter = QSplitter(self)
        vtk_widget = VTKWidget()
        vtk_widget.add_track(track)

        vtk_widget.render_lines()

        chart = MsdChartWidget(track)
        # chart.bar_clicked.connect(vtk_widget.display_points)

        splitter.addWidget(vtk_widget)
        splitter.addWidget(chart)
        splitter.setWindowTitle(track.name)
        self.central_widget.add_widget(splitter)

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

        splitter = QSplitter(self)

        vtk_widget = VTKWidget(self)

        for index, track in enumerate(tracks):
            vtk_widget.add_track(track)
            # self.print(track_pos)
        vtk_widget.render_lines()

        chart = MsdChartWidget(tracks)
        chart.msd_line_clicked.connect(self.display_track)
        # chart.bar_clicked.connect(vtk_widget.display_points)

        splitter.addWidget(vtk_widget)
        splitter.addWidget(chart)
        splitter.setWindowTitle(title)
        self.central_widget.add_widget(splitter)

    def display_msd_tracks(self, tracks, title):
        vtk_widget = VTKWidget(self)

        window = self.find_mdi_child(title)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        for track in tracks:
            vtk_widget.add_track(track)
            # self.print(track_pos)
        vtk_widget.render_lines()

        vtk_widget.setWindowTitle(title)

        splitter = QSplitter(self)

        chart = MsdChartWidget(tracks, title)
        # chart.setWindowTitle(title)
        chart.msd_line_clicked.connect(self.display_track)

        splitter.addWidget(vtk_widget)
        splitter.addWidget(chart)
        self.central_widget.add_widget(splitter)

    def display_channel(self, channel):
        vtk_widget = VTKWidget(self)
        title = channel.name

        window = self.find_mdi_child(title)
        if window:
            self.central_widget.setActiveSubWindow(window)
            return

        for track in channel.tracks:
            vtk_widget.add_track(track)
            # self.print(track_pos)
        vtk_widget.render_lines()

        vtk_widget.setWindowTitle(title)

        splitter = QSplitter(self)

        chart = MsdChartWidget(channel.tracks)
        chart.msd_line_clicked.connect(self.display_track)
        chart.msd_line_clicked.connect(vtk_widget.highlight_track)
        chart.setWindowTitle(f'MSD {title}')

        splitter.addWidget(vtk_widget)
        splitter.addWidget(chart)
        self.central_widget.add_widget(splitter)

    def find_mdi_child(self, title):
        for window in self.central_widget.subWindowList():
            if window.windowTitle() == title:
                return window

        return None
