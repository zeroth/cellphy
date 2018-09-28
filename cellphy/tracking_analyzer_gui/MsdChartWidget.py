import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
from PyQt5.QtSvg import QSvgGenerator

from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QSizePolicy, QSplitter
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtCore import QSize
from PyQt5.QtChart import QChart, QChartView, QSplineSeries, QValueAxis, QScatterSeries
import numpy as np
from cellphy.Analysis import Track, Channel
from .VTKWidget import VTKWidget
from scipy.optimize import curve_fit

def fit_function(_x, d, t):
    return d * np.power(_x, t)


def fit_velocity_function(_x, d, t, v):
    return d * np.power(_x, t) + (np.power(v, 2) * np.power(_x, 2))


class MSDLineSeries(QSplineSeries):
    selected = QtCore.pyqtSignal(Track)

    def __init__(self, track, parent=None):
        QSplineSeries.__init__(self, parent)
        self.clicked.connect(self.__selected)
        self.hovered.connect(self.highlight)
        self.old_pen = None
        self.track = track

        self.y = np.array(list(track.msd(limit=26)))
        self.x = np.array(list(range(0, len(self.y) + 2))) * 3.8

        self.setColor(QColor(track.color[0], track.color[1], track.color[2], 255))
        self.setPen(QPen(QBrush(self.color()), 2))
        self.setName(track.name)
        for i, p in enumerate(self.y):
            self.append(self.x[i], p)

    def __selected(self):
        self.selected.emit(self.track)

    def highlight(self, _, state):
        if state:
            self.old_pen = self.pen()
            self.setPen(QPen(QtCore.Qt.black,  self.old_pen.width()+2))
        elif not state and self.old_pen is not None:
            self.setPen(self.old_pen)

    def max_y(self):
        return self.y.max()


class MsdChartWidget(QMainWindow):
    msd_line_clicked = QtCore.pyqtSignal(Track)

    def __init__(self, tracks, title=None, parent=None):
        QMainWindow.__init__(self, parent)
        self.title = title
        self.chart_view = QChartView(self)

        self.setCentralWidget(self.chart_view)

        self.tracks = tracks
        if type(tracks) is not list:
            self.tracks = [self.tracks]

        self.chart = QChart()

        self.max_y = []

        for track in self.tracks:
            if len(track.time_position_map) < 2:
                continue
            line_series = MSDLineSeries(track)
            line_series.selected.connect(self.msd_line_clicked)
            self.max_y.append(line_series.max_y())
            self.chart.addSeries(line_series)

        if len(self.tracks) < 3:
            name = '-'.join([str(n.track_id) for n in self.tracks])
            _title = f'MSD Analysis {name}'
            self.setWindowTitle(_title)
            self.chart.setTitle(_title)
        else:
            _title = self.title if self.title is not None else f'MSD Analysis'
            self.chart.setTitle(_title)
            self.chart.legend().setVisible(False)
        # self.chart.setAnimationOptions(QChart.SeriesAnimations)

        self.chart.createDefaultAxes()

        axis_x = QValueAxis()
        axis_x.setRange(0, 110)
        axis_x.setTickCount(10)
        axis_x.setLabelFormat("%.2f")
        self.chart.setAxisX(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(self.max_y)+20)
        axis_y.setTickCount(10)
        axis_y.setLabelFormat("%.2f")
        self.chart.setAxisY(axis_y)

        self.chart_view.setChart(self.chart)
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)

        self.tool_bar = self.addToolBar('MSDToolBar')

        self.setup_tool_bar()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

    def setup_tool_bar(self):
        save_image_action = QAction('Export SVG', self)
        save_image_action.triggered.connect(self.save_svg)
        self.tool_bar.addAction(save_image_action)

    def save_svg(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Dialog for Export SVG", QtCore.QDir.homePath(), "SVG (*.svg)")

        if not file:
            return

        target_react = QtCore.QRectF(0.0, 0.0, self.chart_view.sceneRect().size().width(), self.chart_view.sceneRect().size().height());
        svg_generator = QSvgGenerator()
        svg_generator.setFileName(file)
        svg_generator.setSize(self.chart_view.sceneRect().size().toSize())
        svg_generator.setViewBox(self.chart_view.sceneRect())

        painter = QtGui.QPainter(svg_generator)
        self.chart_view.render(painter, target_react, self.chart_view.sceneRect().toRect())
        painter.end()

    def sizeHint(self):
        return QSize(400, 400)


class LineSeries(QSplineSeries):
    # selected = QtCore.pyqtSignal(Track)

    def __init__(self, x, y, color, name, parent=None):
        QSplineSeries.__init__(self, parent)
        # self.clicked.connect(self.__selected)
        self.hovered.connect(self.highlight)
        self.old_pen = None

        self.y = np.array(y)
        self.x = np.array(x)

        self.setColor(QColor(color[0], color[1], color[2], 255))
        self.setPen(QPen(QBrush(self.color()), 2))
        self.setName(name)
        for i, p in enumerate(self.y):
            self.append(self.x[i], p)

    # def __selected(self):
    #     self.selected.emit(self.track)

    def highlight(self, _, state):
        if state:
            self.old_pen = self.pen()
            self.setPen(QPen(QtCore.Qt.black,  self.old_pen.width()+2))
        elif not state and self.old_pen is not None:
            self.setPen(self.old_pen)


class ScatterSeries(QScatterSeries):
    # selected = QtCore.pyqtSignal(Track)

    def __init__(self, x, y, color, name, parent=None):
        QScatterSeries.__init__(self, parent)
        # self.clicked.connect(self.__selected)
        self.hovered.connect(self.highlight)
        self.old_pen = None

        self.y = np.array(y)
        self.x = np.array(x)

        self.setColor(QColor(color[0], color[1], color[2], 255))
        self.setPen(QPen(QBrush(self.color()), 2))
        self.setName(name)
        for i, p in enumerate(self.y):
            self.append(self.x[i], p)

    # def __selected(self):
    #     self.selected.emit(self.track)

    def highlight(self, _, state):
        if state:
            self.old_pen = self.pen()
            self.setPen(QPen(QtCore.Qt.black, self.old_pen.width() + 2))
        elif not state and self.old_pen is not None:
            self.setPen(self.old_pen)


class ChartView(QChartView):
    def __init__(self, parent=None):
        QChartView.__init__(self, parent)

    def sizeHint(self):
        return QSize(400, 400)


class MSDWidget(QMainWindow):
    def __init__(self, source_list, title, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle(title)
        self.title = title

        self.central_widget = QSplitter(self)
        self.setCentralWidget(self.central_widget)

        if type(source_list) is not list:
            source_list = [source_list]

        assert type(source_list[0]) in [Channel, Track]

        if type(source_list[0]) is Channel:
            self.init_channels(source_list)
        else:
            self.init_tracks(source_list)

    def init_channels(self, source_list):
        pass

    def init_tracks(self, source_list):
        vtk_widget = self.get_vtk_widget(source_list)
        self.central_widget.addWidget(vtk_widget)

        msd_widget, msd_widget_velocity = self.get_msd_chart(source_list)

        self.central_widget.addWidget(msd_widget)

        if msd_widget_velocity is not None:
            self.central_widget.addWidget(msd_widget_velocity)

    def get_vtk_widget(self, tracks):
        widget = VTKWidget(self)
        for track in tracks:
            widget.add_track(track)
            # self.print(track_pos)
        widget.render_lines()
        return widget

    def get_msd_chart(self, tracks):
        chart_view = ChartView(self)
        chart = QChart()
        chart_v = QChart()
        max_y = []
        need_velocity = False
        for track in tracks:
            y = np.array(list(track.msd(limit=26)))
            max_y.append(y.max())
            x = np.array(list(range(1, len(y) + 1))) * 3.8
            scattered_line = ScatterSeries(x, y, track.color, track.name)
            chart.addSeries(scattered_line)
            init = np.array([.001, .01])
            best_value, covar = curve_fit(fit_function, x, y, p0=init, maxfev=10000)
            __y = fit_function(x, best_value[0], best_value[1])
            line_series = LineSeries(x, __y, track.color, track.name)
            chart.addSeries(line_series)
            if best_value[1] > 1.4:
                _init = np.array([.001, .01, .01])
                _best_value, _covar = curve_fit(fit_velocity_function, x, y, p0=_init, maxfev=1000000)
                _y = fit_velocity_function(x, _best_value[0], _best_value[1], _best_value[2])
                _line_series = LineSeries(x, _y, track.color, track.name)
                _scattered_line = ScatterSeries(x, y, track.color, track.name)
                chart_v.addSeries(_line_series)
                chart_v.addSeries(_scattered_line)
                need_velocity = True

        chart_view.setChart(chart)

        chart.createDefaultAxes()

        axis_x = QValueAxis()
        axis_x.setRange(0, 110)
        axis_x.setTickCount(10)
        axis_x.setLabelFormat("%.2f")
        chart.setAxisX(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(max_y) + 20)
        axis_y.setTickCount(10)
        axis_y.setLabelFormat("%.2f")
        chart.setAxisY(axis_y)

        chart_view.setRenderHint(QtGui.QPainter.Antialiasing)

        result = None
        if need_velocity:
            chart_view_v = ChartView(self)
            chart_v.createDefaultAxes()

            axis_x_v = QValueAxis()
            axis_x_v.setRange(0, 110)
            axis_x_v.setTickCount(10)
            axis_x_v.setLabelFormat("%.2f")

            axis_y_v = QValueAxis()
            axis_y_v.setRange(0, max(max_y) + 20)
            axis_y_v.setTickCount(10)
            axis_y_v.setLabelFormat("%.2f")

            chart_v.setAxisX(axis_x_v)
            chart_v.setAxisY(axis_y_v)
            chart_view_v.setChart(chart_v)
            chart_view_v.setRenderHint(QtGui.QPainter.Antialiasing)
            result = chart_view_v

        return chart_view, result


