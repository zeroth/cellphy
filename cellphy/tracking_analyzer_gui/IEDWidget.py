from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QFileDialog,QAction, QMainWindow
import PyQt5.QtCore as QtCore
from cellphy.Analysis.Track import Track
from cellphy.Analysis.Channel import Channel


class IEDWidget(QMainWindow):
    track_clicked = QtCore.pyqtSignal(Track)
    display_msd_channel = QtCore.pyqtSignal(Channel)
    display_ied_channel = QtCore.pyqtSignal(Channel)

    def __init__(self, channel, parent=None):
        QMainWindow.__init__(self, parent)

        self.channel = channel
        self.table_widget = QTableWidget()
        self.tool_bar = self.addToolBar('IED ToolBar')
        self.setCentralWidget(self.table_widget)

        self.create_csv_act = QAction('Export')
        self.create_csv_act.triggered.connect(self.export_csv)
        self.tool_bar.addAction(self.create_csv_act)
        self.headers = ['Time', 'Mean', 'Standard Deviation']
        self.prepare_table()

    def prepare_table(self):
        ied = self.channel.get_time_point_mean_and_stdev()
        packets = list(ied.values())
        #
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(self.headers)
        for row, packet in enumerate(packets):
            self.table_widget.setRowCount(row+1)
            for col, val in enumerate(packet):
                table_item = QTableWidgetItem(str(val))
                self.table_widget.setItem(row, col, table_item)

    def export_csv(self):
        _csv = ''
        # get headers 1st
        _csv += ','.join(self.headers) + '\n'

        # now get the data
        for row in range(self.table_widget.rowCount()):
            row_vals = []
            for col in range(self.table_widget.columnCount()):
                row_vals.append(self.table_widget.item(row, col).text())
            _csv += ','.join(row_vals) + '\n'

        file, _ = QFileDialog.getSaveFileName(self, "Select file name IED .csv files",
                                                QtCore.QDir.homePath(), "CSV (*.csv)")

        fd = open(file, 'w')
        fd.write(_csv)
        fd.close()
