from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QFileDialog,QAction, QMainWindow
import PyQt5.QtCore as QtCore


class AlfaTotalTable(QMainWindow):

    def __init__(self, dictionary, title, parent=None):
        QMainWindow.__init__(self, parent)

        self.dictionary = dictionary
        self.table_widget = QTableWidget()
        self.tool_bar = self.addToolBar('IED ToolBar')
        self.setCentralWidget(self.table_widget)

        self.create_csv_act = QAction('Export')
        self.create_csv_act.triggered.connect(self.export_csv)
        self.tool_bar.addAction(self.create_csv_act)
        self.headers = ['Bin', 'Alfa Count', 'Alfa < 1.4 count', 'Alfa > 1.4 count']
        self.prepare_table()
        self.setWindowTitle(title)

    def prepare_table(self):
        self.table_widget.setColumnCount(len(self.headers))
        self.table_widget.setHorizontalHeaderLabels(self.headers)
        row = 0
        for key, value in self.dictionary.items():
            self.table_widget.setRowCount(row+1)

            bin_item = QTableWidgetItem(str(key))
            self.table_widget.setItem(row, 0, bin_item)

            total_item = QTableWidgetItem(str(value['total']))
            self.table_widget.setItem(row, 1, total_item)

            lt_item = QTableWidgetItem(str(value['lt']))
            self.table_widget.setItem(row, 2, lt_item)

            gt_item = QTableWidgetItem(str(value['gt']))
            self.table_widget.setItem(row, 3, gt_item)

            row += 1

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
