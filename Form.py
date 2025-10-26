import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidget,
    QTableWidgetItem, QPushButton, QVBoxLayout, QWidget
)
from PyQt5.QtCore import Qt

class CSVViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DoAnTinHoc")
        self.resize(800, 500)

        self.table = QTableWidget()
        self.button = QPushButton("Choose file")
        self.button.setFixedSize(120,50)
        self.button.clicked.connect(self.readWrite)

        layout = QVBoxLayout()
        layout.addWidget(self.button, alignment=Qt.AlignCenter)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def readWrite(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Please choose a file!", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return

        with open(file_path, newline='', encoding='utf-8') as readfile:
            data= list(csv.reader(readfile))
        if not data:
            return

        self.table.setColumnCount(len(data[0]))
        self.table.setRowCount(len(data)-1)
        self.table.setHorizontalHeaderLabels(data[0])

        for i, row in enumerate(data[1:]):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(value))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CSVViewer()
    viewer.show()
    sys.exit(app.exec_())
