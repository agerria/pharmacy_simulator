from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QSplitter,
)

from ..business import PharmacyDayStatistics

class DayDetailsTab(QWidget):
    day_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.splitter = QSplitter(Qt.Horizontal)

        # Таблица дней
        self.days_table = QTableWidget()
        self.days_table.setColumnCount(5)
        self.days_table.setHorizontalHeaderLabels([
            'День', 'Доход', 'Прибыль', 'Потери', 'Маржинальность'
        ])
        self.days_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.days_table.itemSelectionChanged.connect(self._on_day_selected)

        # Таблицы детализации
        self.details_tabs = QTabWidget()
        self._init_tables()

        self.splitter.addWidget(self.days_table)
        self.splitter.addWidget(self.details_tabs)
        self.splitter.setSizes([400, 600])

        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

    def _init_tables(self):
        # Таблица заказов
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            'Клиент', 'Адрес', 'Тип', 'Статус', 'Сумма', 'Товары',
        ])
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.setSortingEnabled(True)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Таблица склада
        self.warehouse_table = QTableWidget()
        self.warehouse_table.setColumnCount(6)
        self.warehouse_table.setHorizontalHeaderLabels([
            'Лекарство', 'Партии', 'Поставки',
            'Количество', 'Минимум', 'Закупки',
        ])
        self.warehouse_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.details_tabs.addTab(self.orders_table, "📦 Заказы")
        self.details_tabs.addTab(self.warehouse_table, "🏭 Склад")

    def update_days(self, stats: list[PharmacyDayStatistics]):
        self.days_table.setRowCount(len(stats))
        for row, day in enumerate(stats):

            items = [
                QTableWidgetItem(f"День {day.day}"),
                QTableWidgetItem(f"{day.revenue:.0f}₽"),
                QTableWidgetItem(f"{day.profit:.0f}₽"),
                QTableWidgetItem(f"{day.losses:.0f}₽"),
                QTableWidgetItem(f"{day.margin:.1f}%")
            ]

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.days_table.setItem(row, col, item)

    def update_day_details(self, day_data: PharmacyDayStatistics):
        # Заказы
        valid_orders = [o for o in day_data.orders]
        self.orders_table.setRowCount(len(valid_orders))

        for row, order in enumerate(sorted(valid_orders, key=lambda x: x.customer.name)):
            cells = [
                QTableWidgetItem(order.customer.name),
                QTableWidgetItem(order.customer.address),
                QTableWidgetItem(order.type),
                QTableWidgetItem(order.status),
                QTableWidgetItem(f"{order.summary:,.0f}₽" if order.summary else ""),
                QTableWidgetItem(", ".join(f"{med.name}×{qty}" for med, qty in order.requested_medicines.items())),
            ]
            for col, cell in enumerate(cells):
                cell.setFlags(cell.flags() ^ Qt.ItemIsEditable)
                self.orders_table.setItem(row, col, cell)

        # Склад
        self.warehouse_table.setRowCount(len(day_data.warehouse.medicines.items()))
        for row, (med, wm) in enumerate(day_data.warehouse.medicines.items()):
            cells = [
                QTableWidgetItem(med.name),
                QTableWidgetItem(wm.str_batches()),
                QTableWidgetItem(wm.str_awiting()),
                QTableWidgetItem(str(wm.count)),
                QTableWidgetItem(str(med.min_quantity)),
                QTableWidgetItem(str(med.purchase_quantity)),
            ]
            for col, cell in enumerate(cells):
                cell.setFlags(cell.flags() ^ Qt.ItemIsEditable)
                self.warehouse_table.setItem(row, col, cell)

    def _on_day_selected(self):
        if selected := self.days_table.selectedItems():
            self.day_changed.emit(selected[0].row())
