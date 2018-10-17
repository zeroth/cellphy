import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
from PyQt5.QtSvg import QSvgGenerator
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtCore import QSize
from PyQt5.QtChart import QChart, QChartView, QSplineSeries, QValueAxis, QScatterSeries
import numpy as np
from cellphy.Analysis import Track, Channel
from .VTKWidget import VTKWidget


class LineSeries(QSplineSeries):
    selected = QtCore.pyqtSignal(Track)

    def __init__(self, x, y, track, color, name, parent=None):
        QSplineSeries.__init__(self, parent)
        self.clicked.connect(self.__selected)
        self.hovered.connect(self.highlight)
        self.track = track
        self.old_pen = None

        self.y = np.array(y)
        self.x = np.array(x)

        self.setColor(QColor(color[0], color[1], color[2], 255))
        self.setPen(QPen(QBrush(self.color()), 2))
        self.setName(name)
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


class ScatterSeries(QScatterSeries):
    selected = QtCore.pyqtSignal(Track)

    def __init__(self, x, y, track, color, name, parent=None):
        QScatterSeries.__init__(self, parent)
        self.clicked.connect(self.__selected)
        self.hovered.connect(self.highlight)
        self.track = track
        self.old_pen = None

        self.y = np.array(y)
        self.x = np.array(x)

        self.setColor(QColor(color[0], color[1], color[2], 0))
        self.setPen(QPen(QBrush(self.color()), 2))
        self.setBorderColor(QColor(color[0], color[1], color[2], 255))
        self.setMarkerSize(10)
        self.setName(name)
        for i, p in enumerate(self.y):
            self.append(self.x[i], p)

    def __selected(self):
        self.selected.emit(self.track)

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

    def save_svg(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Dialog for Export SVG", QtCore.QDir.homePath(), "SVG (*.svg)")

        if not file:
            return

        target_react = QtCore.QRectF(0.0, 0.0, self.sceneRect().size().width(), self.sceneRect().size().height());
        svg_generator = QSvgGenerator()
        svg_generator.setFileName(file)
        svg_generator.setSize(self.sceneRect().size().toSize())
        svg_generator.setViewBox(self.sceneRect())

        painter = QtGui.QPainter(svg_generator)
        self.render(painter, target_react, self.sceneRect().toRect())
        painter.end()


class ChartViewWrapper(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.chart_view = ChartView()
        self.setCentralWidget(self.chart_view)
        self.tool_bar = self.addToolBar('MSDToolBar')
        save_image_action = QAction('Export SVG', self)
        save_image_action.triggered.connect(self.chart_view.save_svg)
        self.tool_bar.addAction(save_image_action)

    def sizeHint(self):
        return QSize(400, 400)


class MSDWidget(QMainWindow):
    msd_line_clicked = QtCore.pyqtSignal(Track)

    def __init__(self, source_list, title, change_color=True, vtk_on=True, show_alfa_table=False, parent=None):
        QMainWindow.__init__(self, parent)
        self.vtk_on = vtk_on
        self.show_alfa_table = show_alfa_table
        self.setWindowTitle(title)
        self.title = title
        self.change_color = change_color
        self.central_widget = QSplitter(self)
        self.setCentralWidget(self.central_widget)

        if type(source_list) is not list:
            source_list = [source_list]

        assert type(source_list[0]) in [Channel, Track]

        if type(source_list[0]) is Channel:
            self.init_channels(source_list)
        else:
            if self.change_color:
                self.base_channel_color = source_list[0].color.copy()
            self.init_tracks(source_list)

    def init_channels(self, source_list):
        pass

    def init_tracks(self, source_list):
        tracks = []
        for track in source_list:
            if len(track.time_position_map) > 3:
                tracks.append(track)

        msd_widget, msd_widget_velocity, alfa_all, alfa_lt_1_4, \
            alfa_gt_1_4, alfa_gt_1_4_v, alfa_gt_1_4_n = self.get_msd_chart(tracks)

        # keeping this after MSD for change color to take effect
        if self.vtk_on:
            vtk_widget = self.get_vtk_widget(tracks)
            self.central_widget.addWidget(vtk_widget)

        if self.show_alfa_table:
            alfa_table_widget = AlfaWidget(alfa_all, alfa_lt_1_4, alfa_gt_1_4, alfa_gt_1_4_v, alfa_gt_1_4_n)
            self.central_widget.addWidget(alfa_table_widget)

        self.central_widget.addWidget(msd_widget)

        if msd_widget_velocity is not None:
            self.central_widget.addWidget(msd_widget_velocity)

    def get_vtk_widget(self, tracks):
        widget = VTKWidget(self)
        for track in tracks:
            if self.change_color:
                alfa, _ = track.basic_fit()
                widget.add_track(track, updated_color=self.get_alfa_color(alfa))
            else:
                widget.add_track(track)
            # self.print(track_pos)
        widget.render_lines()
        # self.msd_line_clicked.connect(widget.highlight_track)
        return widget

    def get_msd_chart(self, tracks):
        chart_view_wrapper = ChartViewWrapper(self)
        chart = QChart()
        chart.setTitle('Msd & Curve Fit')
        chart_v = QChart()
        chart_v.setTitle('Msd & Curve Fit with Velocity')
        max_y = []
        need_velocity = False
        alfa_all = []
        alfa_lt_1_4 = []
        alfa_gt_1_4 = []
        alfa_gt_1_4_v = []
        alfa_gt_1_4_n = []

        for track in tracks:
            y = np.array(list(track.msd(limit=26)))
            max_y.append(y.max())
            x = np.array(list(range(1, len(y) + 1))) * 3.8
            scattered_line = ScatterSeries(x, y, track, self.base_channel_color if self.change_color else track.color, track.name)
            scattered_line.selected.connect(self.msd_line_clicked)

            chart.addSeries(scattered_line)

            alfa, __y = track.basic_fit()
            alfa_all.append(alfa)
            line_series = LineSeries(x, __y, track, self.get_alfa_color(alfa) if self.change_color else track.color, track.name)
            line_series.selected.connect(self.msd_line_clicked)
            chart.addSeries(line_series)
            if alfa > 1.2:
                alfa_gt_1_4.append(alfa)
                _init = np.array([.001, .01, .01])
                _alfa, _velocity, _y = track.velocity_fit()
                alfa_gt_1_4_n.append(_alfa)
                alfa_gt_1_4_v.append(_velocity)
                _line_series = LineSeries(x, _y, track, self.get_alfa_color(alfa) if self.change_color else track.color, track.name)
                _line_series.selected.connect(self.msd_line_clicked)
                _scattered_line = ScatterSeries(x, y, track, self.base_channel_color if self.change_color else track.color, track.name)
                _scattered_line.selected.connect(self.msd_line_clicked)
                chart_v.addSeries(_line_series)
                chart_v.addSeries(_scattered_line)
                need_velocity = True
            else:
                alfa_lt_1_4.append(alfa)

        chart_view_wrapper.chart_view.setChart(chart)

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

        chart_view_wrapper.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)

        if len(tracks) > 2:
            chart.legend().setVisible(False)

        result = None
        if need_velocity:
            chart_view_w = ChartViewWrapper(self)
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
            chart_view_w.chart_view.setChart(chart_v)
            chart_view_w.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
            result = chart_view_w
            if len(tracks) > 2:
                chart_v.legend().setVisible(False)

        return chart_view_wrapper, result, alfa_all, alfa_lt_1_4, alfa_gt_1_4, alfa_gt_1_4_v, alfa_gt_1_4_n

    def get_alfa_color(self, alfa):
        yellow = [255, 255, 0, 128]
        cyan = [0, 183, 235, 128]
        magenta= [255, 0, 255, 128]

        if alfa < 0.4:
            return yellow
        elif 0.4 <= alfa <= 1.2:
            return cyan
        else:
            return magenta


class AlfaWidget(QMainWindow):
    track_clicked = QtCore.pyqtSignal(Track)
    display_msd_channel = QtCore.pyqtSignal(Channel)
    display_ied_channel = QtCore.pyqtSignal(Channel)

    def __init__(self, alfa, alfa_lt_1_4, alfa_gt_1_4, alfa_gt_1_4_v, alfa_gt_1_4_n, parent=None):
        QMainWindow.__init__(self, parent)

        self.alfa = alfa
        self.alfa_lt_1_4 = alfa_lt_1_4
        self.alfa_gt_1_4 = alfa_gt_1_4
        self.alfa_gt_1_4_v = alfa_gt_1_4_v
        self.alfa_gt_1_4_n = alfa_gt_1_4_n

        self.table_widget = QTableWidget()
        self.tool_bar = self.addToolBar('Alfa ToolBar')
        self.setCentralWidget(self.table_widget)

        self.create_csv_act = QAction('Export')
        self.create_csv_act.triggered.connect(self.export_csv)
        self.tool_bar.addAction(self.create_csv_act)
        self.headers = ['Alfa', 'Alfa < 1.2', 'Alfa > 1.2', 'New Alfa >1.2', 'Velocity']
        self.prepare_table()

    def prepare_table(self):
        self.table_widget.setColumnCount(len(self.headers))
        self.table_widget.setHorizontalHeaderLabels(self.headers)
        for row, alfa in enumerate(self.alfa):
            self.table_widget.setRowCount(row+1)
            table_item = QTableWidgetItem(str(alfa))
            self.table_widget.setItem(row, 0, table_item)

        for row, alt1 in enumerate(self.alfa_lt_1_4):
            if self.table_widget.rowCount() < (row +1):
                self.table_widget.setRowCount(row+1)
            table_item = QTableWidgetItem(str(alt1))
            self.table_widget.setItem(row, 1, table_item)

        for row, agt1 in enumerate(self.alfa_gt_1_4):
            if self.table_widget.rowCount() < (row +1):
                self.table_widget.setRowCount(row+1)
            table_item = QTableWidgetItem(str(agt1))
            self.table_widget.setItem(row, 2, table_item)

        for row, agt1n in enumerate(self.alfa_gt_1_4_n):
            if self.table_widget.rowCount() < (row +1):
                self.table_widget.setRowCount(row+1)
            table_item = QTableWidgetItem(str(agt1n))
            self.table_widget.setItem(row, 3, table_item)

        for row, agt1v in enumerate(self.alfa_gt_1_4_v):
            if self.table_widget.rowCount() < (row +1):
                self.table_widget.setRowCount(row+1)
            table_item = QTableWidgetItem(str(agt1v))
            self.table_widget.setItem(row, 4, table_item)

    def export_csv(self):
        _csv = ''
        # get headers 1st
        _csv += ','.join(self.headers) + '\n'

        # now get the data
        for row in range(self.table_widget.rowCount()):
            row_vals = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item is not None:
                    row_vals.append(item.text())
            _csv += ','.join(row_vals) + '\n'

        file, _ = QFileDialog.getSaveFileName(self, "Save Curve Fit  values .csv files",
                                                QtCore.QDir.homePath(), "CSV (*.csv)")

        fd = open(file, 'w')
        fd.write(_csv)
        fd.close()



# class MSDLineSeries(QSplineSeries):
#     selected = QtCore.pyqtSignal(Track)
#
#     def __init__(self, track, parent=None):
#         QSplineSeries.__init__(self, parent)
#         self.clicked.connect(self.__selected)
#         self.hovered.connect(self.highlight)
#         self.old_pen = None
#         self.track = track
#
#         self.y = np.array(list(track.msd(limit=26)))
#         self.x = np.array(list(range(0, len(self.y) + 2))) * 3.8
#
#         self.setColor(QColor(track.color[0], track.color[1], track.color[2], 255))
#         self.setPen(QPen(QBrush(self.color()), 2))
#         self.setName(track.name)
#         for i, p in enumerate(self.y):
#             self.append(self.x[i], p)
#
#     def __selected(self):
#         self.selected.emit(self.track)
#
#     def highlight(self, _, state):
#         if state:
#             self.old_pen = self.pen()
#             self.setPen(QPen(QtCore.Qt.black,  self.old_pen.width()+2))
#         elif not state and self.old_pen is not None:
#             self.setPen(self.old_pen)
#
#     def max_y(self):
#         return self.y.max()
#
#
# class MsdChartWidget(QMainWindow):
#     msd_line_clicked = QtCore.pyqtSignal(Track)
#
#     def __init__(self, tracks, title=None, parent=None):
#         QMainWindow.__init__(self, parent)
#         self.title = title
#         self.chart_view = QChartView(self)
#
#         self.setCentralWidget(self.chart_view)
#
#         self.tracks = tracks
#         if type(tracks) is not list:
#             self.tracks = [self.tracks]
#
#         self.chart = QChart()
#
#         self.max_y = []
#
#         for track in self.tracks:
#             if len(track.time_position_map) < 2:
#                 continue
#             line_series = MSDLineSeries(track)
#             line_series.selected.connect(self.msd_line_clicked)
#             self.max_y.append(line_series.max_y())
#             self.chart.addSeries(line_series)
#
#         if len(self.tracks) < 3:
#             name = '-'.join([str(n.track_id) for n in self.tracks])
#             _title = f'MSD Analysis {name}'
#             self.setWindowTitle(_title)
#             self.chart.setTitle(_title)
#         else:
#             _title = self.title if self.title is not None else f'MSD Analysis'
#             self.chart.setTitle(_title)
#             self.chart.legend().setVisible(False)
#         # self.chart.setAnimationOptions(QChart.SeriesAnimations)
#
#         self.chart.createDefaultAxes()
#
#         axis_x = QValueAxis()
#         axis_x.setRange(0, 110)
#         axis_x.setTickCount(10)
#         axis_x.setLabelFormat("%.2f")
#         self.chart.setAxisX(axis_x)
#
#         axis_y = QValueAxis()
#         axis_y.setRange(0, max(self.max_y)+20)
#         axis_y.setTickCount(10)
#         axis_y.setLabelFormat("%.2f")
#         self.chart.setAxisY(axis_y)
#
#         self.chart_view.setChart(self.chart)
#         self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
#
#         self.tool_bar = self.addToolBar('MSDToolBar')
#
#         self.setup_tool_bar()
#         self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
#
#     def setup_tool_bar(self):
#         save_image_action = QAction('Export SVG', self)
#         save_image_action.triggered.connect(self.save_svg)
#         self.tool_bar.addAction(save_image_action)
#
#     def save_svg(self):
#         file, _ = QFileDialog.getSaveFileName(self, "Save Dialog for Export SVG", QtCore.QDir.homePath(), "SVG (*.svg)")
#
#         if not file:
#             return
#
#         target_react = QtCore.QRectF(0.0, 0.0, self.chart_view.sceneRect().size().width(), self.chart_view.sceneRect().size().height());
#         svg_generator = QSvgGenerator()
#         svg_generator.setFileName(file)
#         svg_generator.setSize(self.chart_view.sceneRect().size().toSize())
#         svg_generator.setViewBox(self.chart_view.sceneRect())
#
#         painter = QtGui.QPainter(svg_generator)
#         self.chart_view.render(painter, target_react, self.chart_view.sceneRect().toRect())
#         painter.end()
#
#     def sizeHint(self):
#         return QSize(400, 400)