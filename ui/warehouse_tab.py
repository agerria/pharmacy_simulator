import random
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QTabWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .config_tab import ConfigTab


class WarehouseConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()

        self.meds_tab = ConfigTab(
            9,
            [
                'Название', 'Количество', 'Дозировка', 'Тип',
                'Срок годности', 'Оптовая цена', 'Группа',
                'Закупочное количество', 'Минимальное количество'
            ],
            self.generate_medicines
        )
        self.meds_tab.generate_data()

        self.customers_tab = ConfigTab(
            6,
            [
                'Имя', 'Телефон', 'Адрес',
                'Дисконтная карта', 'Регулярные заказы', 'Периодичность'
            ],
            self.generate_customers
        )
        self.customers_tab.generate_data()

        self.tabs.addTab(self.meds_tab, "💊 Лекарства")
        self.tabs.addTab(self.customers_tab, "👥 Постоянные клиенты")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def generate_medicines(self, table, rows):
        types = ["Таблетки", "Спрей", "Мазь", "Капли"]
        groups = ["Сердечные", "Антибиотики", "Обезболивающие"]

        table.setRowCount(rows)
        for row in range(rows):
            data = [
                f"Лекарство {row+1}",
                str(random.randint(50, 200)),
                str(random.choice([50, 100, 200])),
                random.choice(types),
                str(random.randint(10, 31)),
                f"{random.uniform(10, 100):.2f}",
                random.choice(groups),
                str(random.randint(20, 100)),
                str(random.randint(5, 20))
            ]
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                if col in [7, 8]:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, col, item)

    def generate_customers(self, table, rows):
        streets = ["Ленина", "Гагарина", "Советская"]
        meds_data = self.meds_tab.get_data()
        med_names = [row[0] for row in meds_data if row]

        table.setRowCount(rows)
        for row in range(rows):
            discount = "Да" if random.random() > 0.5 else "Нет"
            orders = ", ".join(
                f"{random.choice(med_names)}:{random.randint(1,5)}"
                for _ in range(random.randint(1,3))
            ) if med_names else ""

            data = [
                f"Постоянный {row+1}",
                f"+7{random.randint(9000000000, 9999999999)}",
                f"ул. {random.choice(streets)}, {random.randint(1, 100)}",
                discount,
                orders,
                str(random.randint(2, 7))
            ]
            for col, value in enumerate(data):
                table.setItem(row, col, QTableWidgetItem(value))

    def get_medicines_data(self):
        return self.meds_tab.get_data()

    def get_customers_data(self):
        return self.customers_tab.get_data()
