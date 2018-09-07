import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
from PyQt5.QtChart import QChart, QChartView,  QBarSet,  QBarSeries, QBarCategoryAxis
from cellphy.Analysis.functions import jump_analysis


class JumpChartWidget(QChartView):
    bar_clicked = QtCore.pyqtSignal(list, float, str)

    def __init__(self, track, parent=None):
        QChartView.__init__(self, parent)
        self.track = track
        self.points = jump_analysis(list(track.time_position_map.values()))
        self.bar_set = QBarSet("Time Points")
        for p in self.points:
            self.bar_set.append(p)

        self.bar_set.clicked.connect(self.__bar_clicked)

        self.bar_series = QBarSeries()
        self.bar_series.append(self.bar_set)

        self.chart = QChart()
        self.chart.addSeries(self.bar_series)
        self.chart.setTitle(f'Jump Analysis for {track.name}')
        self.chart.setAnimationOptions(QChart.SeriesAnimations)

        self.axis = QBarCategoryAxis()
        self.axis.append([str(i) for i in range(1, len(self.points)+1)])

        self.chart.createDefaultAxes()
        self.chart.setAxisX(self.axis, self.bar_series)

        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(QtCore.Qt.AlignBottom)

        self.setChart(self.chart)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

    def __bar_clicked(self, index):
        time_points = list(self.track.time_position_map.keys())[index:index+2]
        self.bar_clicked.emit(time_points, self.track.track_id, str(self.bar_set.at(index)))
