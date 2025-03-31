import csv
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSpinBox,
    QFileDialog,
    QHeaderView,
)

class ConfigTab(QWidget):
    def __init__(self, columns, headers, generate_callback=None):
        super().__init__()
        self.columns = columns
        self.headers = headers
        self.generate_callback = generate_callback

        self.table = QTableWidget()
        self.table.setColumnCount(columns)
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(20)

        self.add_btn = QPushButton("＋")
        self.del_btn = QPushButton("🗑")
        self.load_btn = QPushButton("📂")
        self.save_btn = QPushButton("💾")
        self.generate_btn = QPushButton("🎲")

        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Строк:"))
        control_layout.addWidget(self.rows_spin)
        control_layout.addWidget(self.add_btn)
        control_layout.addWidget(self.del_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.load_btn)
        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.generate_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.delete_row)
        self.load_btn.clicked.connect(self.load_csv)
        self.save_btn.clicked.connect(self.save_csv)
        self.generate_btn.clicked.connect(self.generate_data)

        self._setup_validators()

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col in range(self.columns):
            self.table.setItem(row, col, QTableWidgetItem(""))

    def delete_row(self):
        if (row := self.table.currentRow()) >= 0:
            self.table.removeRow(row)

    def load_csv(self):
        if filename := self._get_file_open():
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.table.setRowCount(0)
                for row_idx, row in enumerate(reader):
                    self.table.insertRow(row_idx)
                    for col in range(min(self.columns, len(row))):
                        self.table.setItem(row_idx, col, QTableWidgetItem(row[col].strip()))

    def save_csv(self):
        if filename := self._get_file_save():
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                for row in range(self.table.rowCount()):
                    writer.writerow([
                        self.table.item(row, col).text().strip()
                        if self.table.item(row, col) else ""
                        for col in range(self.columns)
                    ])

    def generate_data(self):
        if self.generate_callback:
            self.generate_callback(self.table, self.rows_spin.value())

    def get_data(self):
        return [
            [self.table.item(row, col).text().strip()
             if self.table.item(row, col) else ""
             for col in range(self.columns)]
            for row in range(self.table.rowCount())
        ]

    def _get_file_open(self):
        return QFileDialog.getOpenFileName(self, "Открыть CSV", "", "CSV Files (*.csv)")[0]

    def _get_file_save(self):
        return QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV Files (*.csv)")[0]

    def _setup_validators(self):
        numeric_columns = [1, 4, 7, 8]
        for col in numeric_columns:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.EditRole, int(item.text()) if item.text() else 0)
