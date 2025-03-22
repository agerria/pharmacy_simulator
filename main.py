# Часть 1: Импорты и настройки
import matplotlib
matplotlib.use('Qt5Agg')  # Явное указание бэкенда

import sys
import random
import csv
from collections import defaultdict
# Часть 1: Импорты и настройки
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QSplitter, QFormLayout, QGroupBox, QPushButton,
    QLabel, QTextEdit, QListWidget, QSpinBox, QLineEdit, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QProgressDialog  # <-- Добавлено здесь
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QDoubleValidator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt

# Общие настройки для matplotlib
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 9,
    'figure.autolayout': True
})

# Часть 2: Классы данных
class Medicine:
    def __init__(self, name, quantity, dosage, type_, expiration_days,
                 wholesale, group, purchase_quantity, min_quantity):
        # Добавляем обработку пустых значений и значений по умолчанию
        self.name = name
        self.quantity = int(quantity) if quantity else 0
        self.dosage = dosage
        self.type = type_
        self.expiration_days = int(expiration_days) if expiration_days else 30
        self.wholesale = float(wholesale) if wholesale else 0.0
        self.group = group
        self.purchase_quantity = int(purchase_quantity) if purchase_quantity else 20
        self.min_quantity = int(min_quantity) if min_quantity else 5

    def is_expired(self):
        return self.expiration_days <= 0

    def is_discounted(self):
        return self.expiration_days <= 30

    def retail_price(self, markup):
        price = self.wholesale * (1 + markup/100)
        return price * 0.5 if self.is_discounted() else price

class Customer:
    def __init__(self, name, phone, address, discount_card=False):
        self.name = name
        self.phone = phone
        self.address = address
        self.discount_card = discount_card
        self.orders = []

class RegularCustomer(Customer):
    def __init__(self, name, phone, address, discount_card=False, regular_orders=None, periodicity=3):
        super().__init__(name, phone, address, discount_card)
        self.regular_orders = regular_orders or []
        self.periodicity = periodicity
        self.next_order_day = periodicity  # Первый заказ в день равный периодичности

    def needs_order(self, day):
        return day == self.next_order_day

    def update_schedule(self, day):
        if day == self.next_order_day:
            self.next_order_day += self.periodicity

# Часть 3: Классы бизнес-логики
class Order:
    def __init__(self, customer, items, is_regular=False):
        self.customer = customer
        self.items = items
        self.is_regular = is_regular
        self.total = 0.0
        self.delivered = False
        self.discount = 0
        self.status = "created"  # created, processed, delivered, canceled

    def calculate_total(self, markup):
        """Расчет стоимости заказа с учетом наценки и скидок"""
        self.total = sum(
            med.retail_price(markup) * qty
            for med, qty in self.items
        )
        return self.total

class Warehouse:
    def __init__(self):
        self.medicines = []
        self.restock_orders = []

    def add_medicine(self, medicine):
        self.medicines.append(medicine)

    def process_restock(self):
        """Обработка заказов на пополнение запасов"""
        for i in reversed(range(len(self.restock_orders))):
            med, qty, days = self.restock_orders[i]
            if days == 0:
                # Добавляем новую партию с полным сроком годности
                new_med = Medicine(
                    name=med.name,
                    quantity=qty,
                    dosage=med.dosage,
                    type_=med.type,
                    expiration_days=med.expiration_days,
                    wholesale=med.wholesale,
                    group=med.group,
                    purchase_quantity=med.purchase_quantity,
                    min_quantity=med.min_quantity
                )
                self.medicines.append(new_med)
                del self.restock_orders[i]
            else:
                self.restock_orders[i] = (med, qty, days-1)

    def check_restock(self):
        """Проверка необходимости заказа новых партий"""
        for med in self.medicines:
            # Проверяем что нет активных заказов на это лекарство
            has_active_order = any(m.name == med.name for m, _, _ in self.restock_orders)

            if med.quantity < med.min_quantity and not has_active_order:
                self.restock_orders.append((
                    med,
                    med.purchase_quantity,
                    random.randint(1, 3)
                ))

    def remove_expired(self):
        """Удаление просроченных лекарств и расчет потерь"""
        total_loss = 0.0
        expired_meds = []

        for med in self.medicines[:]:
            if med.is_expired():
                total_loss += med.quantity * med.wholesale
                expired_meds.append(med)
                self.medicines.remove(med)

        return total_loss, expired_meds

class Courier:
    def __init__(self):
        self.orders = []
        self.max_orders = 15  # Максимум заказов в день

    def deliver(self):
        """Обработка доставки заказов"""
        delivered = []
        # Сначала доставляем регулярные заказы
        regular_orders = [o for o in self.orders if o.is_regular]
        # Затем остальные, отсортированные по стоимости
        other_orders = sorted(
            [o for o in self.orders if not o.is_regular],
            key=lambda x: x.total,
            reverse=True
        )

        # Объединяем и берем первые max_orders
        all_orders = regular_orders + other_orders
        for order in all_orders[:self.max_orders]:
            order.delivered = True
            delivered.append(order)

        self.orders = []
        return delivered

# Часть 4: Класс Simulation
class Simulation:
    def __init__(self, params, medicines_data, customers_data):
        self.days = params['days']
        self.couriers_cnt = params['couriers']
        self.markup = params['markup']
        self.discount_card_percent = params.get('discount_card', 5)
        self.warehouse = Warehouse()
        self.customers = []
        self.daily_stats = []
        self.orders = []
        self.total_income = 0.0
        self.total_profit = 0.0
        self.total_losses = 0.0

        # Инициализация лекарств
        for i, med_data in enumerate(medicines_data):
            self.warehouse.add_medicine(Medicine(
                name=f"Лекарство {i+1}",
                quantity=int(med_data[1]),
                dosage=med_data[2],
                type_=med_data[3],
                expiration_days=int(med_data[4]),
                wholesale=float(med_data[5]),
                group=med_data[6],
                purchase_quantity=int(med_data[7]),
                min_quantity=int(med_data[8])
            ))

        # Инициализация клиентов
        for cust_data in customers_data:
            try:
                orders = []
                for pair in cust_data[4].split(','):
                    name, qty = pair.split(':')
                    med = next((m for m in self.warehouse.medicines if m.name == name.strip()), None)
                    if med: orders.append((med, int(qty)))

                self.customers.append(RegularCustomer(
                    name=cust_data[0],
                    phone=cust_data[1],
                    address=cust_data[2],
                    discount_card=cust_data[3] == "Да",
                    regular_orders=orders,
                    periodicity=int(cust_data[5]) if cust_data[5] else 3
                ))
            except Exception as e:
                print(f"Ошибка создания клиента: {e}")

        # Генерация случайных клиентов
        self._generate_random_customers(1000)  # 20 случайных клиентов

        # Инициализация курьеров
        self.couriers = [Courier() for _ in range(self.couriers_cnt)]

    def _generate_random_customers(self, count):
        """Генерация случайных непостоянных клиентов"""
        streets = ["Ленина", "Гагарина", "Советская"]
        for i in range(count):
            self.customers.append(Customer(
                name=f"Клиент {i+1}",
                phone=f"+7{random.randint(9000000000, 9999999999)}",
                address=f"ул. {random.choice(streets)}, {random.randint(1, 100)}",
                discount_card=random.random() > 0.7
            ))

    def run_day(self, day):
        # Обработка поставок в начале дня
        self.warehouse.process_restock()

        # Генерация заказов
        orders = self._generate_orders(day)
        processed_orders = self._process_orders(orders)
        self.orders.extend(processed_orders)
        delivered_orders = self._deliver_orders()

        # Учет финансовых показателей
        day_income = sum(order.total for order in delivered_orders)
        day_profit = day_income - sum(
            med.wholesale * qty
            for order in delivered_orders
            for med, qty in order.items
        )

        # Списание просроченных
        day_loss, expired_meds = self.warehouse.remove_expired()

        # Обновление статистики
        self.total_income += day_income
        self.total_profit += day_profit
        self.total_losses += day_loss

        # Сохранение дневной статистики
        self.daily_stats.append({
            'day': day + 1,
            'income': day_income,
            'profit': day_profit,
            'losses': day_loss,
            'orders': delivered_orders,
            'expired': expired_meds,
            'warehouse': self._get_warehouse_state()
        })

        # Проверка необходимости пополнения
        self.warehouse.check_restock()

   # В классе Simulation
    def _generate_orders(self, day):
        orders = []

        # 1. Регулярные заказы
        for customer in self.customers:
            if isinstance(customer, RegularCustomer) and customer.needs_order(day):
                items = []
                for med, qty in customer.regular_orders:
                    available = min(qty, med.quantity)
                    if available > 0:
                        items.append((med, available))
                if items:
                    order = Order(customer, items, is_regular=True)
                    order.calculate_total(self.markup)
                    orders.append(order)
                customer.update_schedule(day)

        # 2. Случайные заказы для всех клиентов
        for customer in self.customers:
            # Рассчет вероятности заказа
            base_prob = 0.05 - (self.markup - 25) * (0.04 / 75)
            base_prob = max(0.01, min(0.05, base_prob))  # Ограничиваем 1-5%

            # Повышение вероятности для уцененных товаров
            if any(m.is_discounted() for m in self.warehouse.medicines):
                base_prob *= 1.5

            if random.random() > base_prob:
                continue

            # Выбор лекарства
            med = self._choose_medicine_for_order()
            if not med:
                continue

            # Формирование заказа
            requested_qty = random.randint(1, 5)
            order = Order(customer, [(med, requested_qty)])
            orders.append(order)

        return orders

    def _choose_medicine_for_order(self):
        """Выбор лекарства с приоритетом уцененных"""
        discounted = [m for m in self.warehouse.medicines if m.is_discounted()]
        if discounted:
            return random.choice(discounted)
        return random.choice(self.warehouse.medicines) if self.warehouse.medicines else None

    def _process_orders(self, orders):
        """Обработка заказов с фильтрацией пустых"""
        valid_orders = []
        for order in orders:
            valid_items = []
            for med, qty in order.items:
                available = min(qty, med.quantity)
                if available > 0:
                    valid_items.append((med, available))
                    med.quantity -= available  # Списываем только фактическое количество

            if valid_items:
                order.items = valid_items
                order.calculate_total(self.markup)
                valid_orders.append(order)
        return valid_orders  # Возвращаем только заказы с товарами

    def _deliver_orders(self):
        """Доставка с приоритетом дорогих заказов"""
        # Сортировка по убыванию суммы
        sorted_orders = sorted(
            self.orders,
            key=lambda x: x.total,
            reverse=True
        )

        # Распределение между курьерами
        delivered = []
        for i, courier in enumerate(self.couriers):
            courier_orders = sorted_orders[i::self.couriers_cnt]
            delivered += courier.deliver()

        return delivered

    def _apply_discounts(self, order):
        discount = 0
        if order.customer.discount_card:
            discount += self.discount_card_percent
        if order.total > 1000:
            discount += 3
        discount = min(discount, 9)
        order.total *= (1 - discount / 100)
        order.discount = discount


    def _get_warehouse_state(self):
        """Возвращает состояние склада с учетом новых параметров"""
        state = []
        for med in self.warehouse.medicines:
            # Добавляем недостающие ключи
            state.append({
                'name': med.name,
                'quantity': med.quantity,
                'min_quantity': med.min_quantity,
                'purchase_quantity': med.purchase_quantity,  # Добавлено
                'restock': self._get_restock_info(med),
                'expiration': med.expiration_days
            })
        return state

    def _get_restock_info(self, med):
        for m, qty, days in self.warehouse.restock_orders:
            if m.name == med.name:
                return f"{qty}:{days}"
        return ""

# Часть 5: Графические компоненты
class StatsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax2 = self.ax.twinx()

        # Настройки осей
        self.ax.set_ylabel('Рубли (₽)', fontsize=10)
        self.ax2.set_ylabel('Количество', fontsize=10)
        self.ax2.yaxis.set_label_coords(1.1, 0.5)
        self.ax.grid(True, linestyle='--', alpha=0.5)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, days, profit, losses, orders, delivered):
        try:
            # Очистка предыдущих графиков
            self.ax.cla()
            self.ax2.cla()

            # График прибыли/потерь
            self.ax.plot(days, profit, 'g-', label='Прибыль', marker='o')
            self.ax.plot(days, losses, 'r--', label='Потери', marker='x')

            # Графики заказов
            x = [d-0.2 for d in days]
            bars1 = self.ax2.bar(x, orders, 0.4, label='Все заказы', alpha=0.5)
            x = [d+0.2 for d in days]
            bars2 = self.ax2.bar(x, delivered, 0.4, label='Доставленные', alpha=0.5)

            # Настройки оформления
            self.ax.set_xlabel('Дни', fontsize=10)
            self.ax.set_title('Финансовые показатели и заказы', fontsize=12)

            # Легенда
            lines, labels = self.ax.get_legend_handles_labels()
            bars, bar_labels = self.ax2.get_legend_handles_labels()
            self.ax.legend(lines + bars, labels + bar_labels, loc='upper left')

            # Форматирование
            self.ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}₽"))
            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Ошибка графиков: {str(e)}")

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
        self.splitter.setSizes([300, 700])

        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

    def _init_tables(self):
        # Таблица заказов
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            'Клиент', 'Адрес', 'Тип', 'Товары', 'Сумма', 'Доставлен'
        ])
        self.orders_table.setSortingEnabled(True)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Таблица склада
        self.warehouse_table = QTableWidget()
        self.warehouse_table.setColumnCount(6)
        self.warehouse_table.setHorizontalHeaderLabels([
            'Лекарство', 'Количество', 'Минимум', 'Закупки',
            'Поставки', 'Срок годности'
        ])
        self.warehouse_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.details_tabs.addTab(self.orders_table, "📦 Заказы")
        self.details_tabs.addTab(self.warehouse_table, "🏭 Склад")

    def update_days(self, stats):
        self.days_table.setRowCount(len(stats))
        for row, day in enumerate(stats):
            margin = (day['profit'] / day['income']) * 100 if day['income'] > 0 else 0

            items = [
                QTableWidgetItem(f"День {day['day']}"),
                QTableWidgetItem(f"{day['income']:,.0f}₽"),
                QTableWidgetItem(f"{day['profit']:,.0f}₽"),
                QTableWidgetItem(f"{day['losses']:,.0f}₽"),
                QTableWidgetItem(f"{margin:.1f}%")
            ]

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.days_table.setItem(row, col, item)

    def update_day_details(self, day_data):
        # Заказы
        valid_orders = [o for o in day_data['orders'] if o.total > 0]
        self.orders_table.setRowCount(len(valid_orders))
        for row, order in enumerate(sorted(valid_orders, key=lambda x: x.customer.name)):
            items = [
                QTableWidgetItem(order.customer.name),
                QTableWidgetItem(order.customer.address),
                QTableWidgetItem("✓" if order.is_regular else ""),
                QTableWidgetItem(", ".join(f"{med.name}×{qty}" for med, qty in order.items)),
                QTableWidgetItem(f"{order.total:,.0f}₽"),
                QTableWidgetItem("✓" if order.delivered else "✗")
            ]
            for col, item in enumerate(items):
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.orders_table.setItem(row, col, item)
            status_icon = "✓" if order.delivered else "✗" if order.status == "canceled" else "⌛"
            self.orders_table.setItem(row, 5, QTableWidgetItem(status_icon))

        # Склад
        self.warehouse_table.setRowCount(len(day_data['warehouse']))
        for row, item in enumerate(day_data['warehouse']):
            cells = [
                QTableWidgetItem(item['name']),
                QTableWidgetItem(str(item['quantity'])),
                QTableWidgetItem(str(item['min_quantity'])),
                QTableWidgetItem(str(item['purchase_quantity'])),  # Теперь ключ существует
                QTableWidgetItem(item['restock']),
                QTableWidgetItem(f"{item['expiration']} дн.")
            ]
            for col, cell in enumerate(cells):
                cell.setFlags(cell.flags() ^ Qt.ItemIsEditable)
                self.warehouse_table.setItem(row, col, cell)

    def _on_day_selected(self):
        if selected := self.days_table.selectedItems():
            self.day_changed.emit(selected[0].row())

# Часть 6: Конфигурация склада
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
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Элементы управления
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(20)

        self.add_btn = QPushButton("＋ Добавить")
        self.del_btn = QPushButton("🗑 Удалить")
        self.load_btn = QPushButton("📂 Загрузить")
        self.save_btn = QPushButton("💾 Сохранить")
        self.generate_btn = QPushButton("🎲 Сгенерировать")

        # Layout
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

        # Сигналы
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
        # Для колонок с числовыми значениями
        numeric_columns = [1, 4, 7, 8]  # Пример для лекарств
        for col in numeric_columns:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.EditRole, int(item.text()) if item.text() else 0)


class WarehouseConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()

        # Вкладка лекарств
        self.meds_tab = ConfigTab(
            9,
            [
                'Название', 'Количество', 'Дозировка', 'Тип',
                'Срок годности', 'Оптовая цена', 'Группа',
                'Закупочное количество', 'Минимальное количество'
            ],
            self.generate_medicines
        )

        # Вкладка клиентов (только постоянные)
        self.customers_tab = ConfigTab(
            6,
            [
                'Имя', 'Телефон', 'Адрес',
                'Дисконтная карта', 'Регулярные заказы', 'Периодичность'
            ],
            self.generate_customers
        )

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
                str(random.randint(10, 365)),
                f"{random.uniform(10, 100):.2f}",
                random.choice(groups),
                str(random.randint(20, 100)),
                str(random.randint(5, 20))
            ]
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                if col in [7, 8]:  # Для числовых колонок
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

# Часть 7: Главное окно приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sim = None
        self.init_ui()
        self.setWindowTitle("Аптека: Моделирование доставки")
        self.setGeometry(100, 100, 1400, 800)

    def init_ui(self):
        # Основной контейнер
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Вкладки
        self.tabs = QTabWidget()
        self._init_simulation_tab()
        self._init_config_tab()

        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def _init_config_tab(self):
        self.config_tab = WarehouseConfigTab()
        self.tabs.addTab(self.config_tab, "⚙️ Конфигурация")

    def _init_simulation_tab(self):
        sim_tab = QWidget()
        layout = QVBoxLayout()

        # Панель управления
        control_panel = QGroupBox("Параметры моделирования")
        form = QFormLayout()

        self.days_spin = QSpinBox()
        self.days_spin.setRange(10, 25)

        self.couriers_spin = QSpinBox()
        self.couriers_spin.setRange(3, 9)

        self.markup_edit = QLineEdit("25")
        self.markup_edit.setValidator(QDoubleValidator(0, 100, 2))

        self.discount_edit = QLineEdit("5")
        self.discount_edit.setValidator(QDoubleValidator(0, 100, 2))

        form.addRow("Дни моделирования:", self.days_spin)
        form.addRow("Количество курьеров:", self.couriers_spin)
        form.addRow("Розничная наценка (%):", self.markup_edit)
        form.addRow("Скидка по карте (%):", self.discount_edit)

        control_panel.setLayout(form)

        # Кнопки
        self.run_btn = QPushButton("▶️ Запустить")
        self.run_btn.clicked.connect(self.start_simulation)

        # Визуализация
        self.stats_tab = StatsTab()
        self.details_tab = DayDetailsTab()
        results_tabs = QTabWidget()
        results_tabs.addTab(self.stats_tab, "📊 Графики")
        results_tabs.addTab(self.details_tab, "📅 Детализация")

        # Итоги
        self.results_label = QLabel()
        self.results_label.setStyleSheet("font-size: 14px; padding: 10px;")

        # Сборка layout
        layout.addWidget(control_panel)
        layout.addWidget(self.run_btn)
        layout.addWidget(results_tabs)
        layout.addWidget(self.results_label)

        sim_tab.setLayout(layout)
        self.tabs.addTab(sim_tab, "📈 Моделирование")

        # Сигналы
        self.details_tab.day_changed.connect(self.show_day_details)

    def start_simulation(self):
        try:
            params = {
                'days': self.days_spin.value(),
                'couriers': self.couriers_spin.value(),
                'markup': float(self.markup_edit.text()),
                'discount_card': float(self.discount_edit.text())
            }

            medicines = self.config_tab.get_medicines_data()
            customers = self.config_tab.get_customers_data()

            self.sim = Simulation(params, medicines, customers)

            # Прогресс-бар
            progress = QProgressDialog("Моделирование...", "Отмена", 0, params['days'], self)
            progress.setWindowModality(Qt.WindowModal)

            for day in range(params['days']):
                if progress.wasCanceled():
                    break
                self.sim.run_day(day)
                progress.setValue(day+1)
                QApplication.processEvents()

            self.update_visualization()
            progress.close()

        except Exception as e:
            raise e
            QMessageBox.critical(self, "Ошибка", f"Ошибка выполнения: {str(e)}")

    def update_visualization(self):
        if not self.sim:
            return

        days = [d['day'] for d in self.sim.daily_stats]
        profit = [d['profit'] for d in self.sim.daily_stats]
        losses = [d['losses'] for d in self.sim.daily_stats]
        orders = [len(d['orders']) for d in self.sim.daily_stats]
        delivered = [sum(1 for o in d['orders'] if o.delivered) for d in self.sim.daily_stats]

        # Графики
        self.stats_tab.plot(days, profit, losses, orders, delivered)

        # Детализация
        self.details_tab.update_days(self.sim.daily_stats)

        # Итоговая статистика
        margin = (self.sim.total_profit / self.sim.total_income * 100) if self.sim.total_income > 0 else 0
        text = (
            f"📈 Общий доход: {self.sim.total_income:,.0f}₽\n"
            f"💰 Чистая прибыль: {self.sim.total_profit:,.0f}₽\n"
            f"📉 Потери: {self.sim.total_losses:,.0f}₽\n"
            f"🎯 Маржинальность: {margin:.1f}%\n"
            f"🚚 Средняя загрузка курьеров: {sum(len(c.orders) for c in self.sim.couriers)/self.sim.couriers_cnt:.1f}"
        )
        self.results_label.setText(text)

    def show_day_details(self, day_idx):
        if self.sim and 0 <= day_idx < len(self.sim.daily_stats):
            self.details_tab.update_day_details(self.sim.daily_stats[day_idx])

# Часть 8: Запуск приложения
if __name__ == "__main__":
    # Создание и настройка приложения
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Создание и отображение главного окна
    window = MainWindow()
    window.show()

    # Запуск основного цикла
    sys.exit(app.exec_())