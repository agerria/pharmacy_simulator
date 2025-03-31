from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QSpinBox,
    QLineEdit,
    QGridLayout,
)
from PyQt5.QtGui import QDoubleValidator

import matplotlib
import matplotlib.pyplot as plt

from .day_details_tab import DayDetailsTab
from .stats_tab import StatsTab
from .warehouse_tab import WarehouseConfigTab

from ..business import Simulation, SimulationParams, PharmacyDayStatistics


matplotlib.use('Qt5Agg')
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 9,
    'figure.autolayout': True
})

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setWindowTitle('Аптека: Моделирование доставки')
        self.setGeometry(100, 100, 1400, 800)

        self.sim = None
        self.statistics: list[PharmacyDayStatistics] = []

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self._init_simulation_tab()
        self._init_config_tab()

        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def _init_config_tab(self):
        self.config_tab = WarehouseConfigTab()
        self.tabs.addTab(self.config_tab, '\u2699 Конфигурация')

    def _init_simulation_tab(self):
        sim_tab = QWidget()
        layout = QVBoxLayout()

        self.days_spin = QSpinBox()
        self.days_spin.setRange(10, 25)

        self.couriers_spin = QSpinBox()
        self.couriers_spin.setRange(3, 9)

        self.markup_edit = QLineEdit('25')
        self.markup_edit.setValidator(QDoubleValidator(0, 100, 2))

        self.discount_edit = QLineEdit('5')
        self.discount_edit.setValidator(QDoubleValidator(0, 100, 2))

        self.base_orders = QSpinBox()
        self.base_orders.setRange(1, 100)

        self.sensitivity = QLineEdit('5')
        self.sensitivity.setValidator(QDoubleValidator(0, 100, 2))

        control_panel = QGroupBox('Параметры моделирования')
        grid = QGridLayout()

        grid.addWidget(QLabel('Дни моделирования:'), 0, 0)
        grid.addWidget(self.days_spin, 0, 1)
        grid.addWidget(QLabel('Количество курьеров:'), 1, 0)
        grid.addWidget(self.couriers_spin, 1, 1)

        grid.addWidget(QLabel('Розничная наценка (%):'), 0, 2)
        grid.addWidget(self.markup_edit, 0, 3)
        grid.addWidget(QLabel('Скидка по карте (%):'), 1, 2)
        grid.addWidget(self.discount_edit, 1, 3)

        grid.addWidget(QLabel('Базовое количество заказов:'), 0, 4)
        grid.addWidget(self.base_orders, 0, 5)
        grid.addWidget(QLabel('Чувствительность наценки (%):'), 1, 4)
        grid.addWidget(self.sensitivity, 1, 5)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(5, 1)
        grid.setHorizontalSpacing(15)

        control_panel.setLayout(grid)

        self.run_btn = QPushButton('\u25B6 Запустить')
        self.run_btn.clicked.connect(self.start_simulation)

        self.stats_tab = StatsTab()
        self.details_tab = DayDetailsTab()
        results_tabs = QTabWidget()
        results_tabs.addTab(self.stats_tab, '📊 Графики')
        results_tabs.addTab(self.details_tab, '📅 Детализация')

        self.results_label = QLabel()
        self.results_label.setStyleSheet('font-size: 14px; padding: 10px;')

        layout.addWidget(control_panel)
        layout.addWidget(self.run_btn)
        layout.addWidget(results_tabs)
        layout.addWidget(self.results_label)

        sim_tab.setLayout(layout)
        self.tabs.addTab(sim_tab, '📈 Моделирование')

        self.details_tab.day_changed.connect(self.show_day_details)

    def start_simulation(self):
        try:
            params = SimulationParams(
                days = self.days_spin.value(),
                couriers = self.couriers_spin.value(),
                retail_margin = float(self.markup_edit.text()) / 100,
                card_discount = float(self.discount_edit.text()) / 100,
                base_orders = self.base_orders.value(),
                sensitivity = float(self.sensitivity.text()) / 100,
            )

            medicines = self.config_tab.get_medicines_data()
            customers = self.config_tab.get_customers_data()

            self.sim = Simulation(params, medicines, customers)

            self.statistics = self.sim.run()
            self.update_visualization()

        except Exception as e:
            raise e

    def update_visualization(self):
        if not self.sim:
            return

        statistics = self.statistics

        days = [s.day for s in statistics]
        profit = [s.profit for s in statistics]
        losses = [s.losses for s in statistics]
        orders = [len(s.orders) for s in statistics]
        delivered = [
            sum(1 for o in s.orders if o.is_delivered)
            for s in statistics
        ]

        self.stats_tab.plot(days, profit, losses, orders, delivered)

        self.details_tab.update_days(statistics)

        total = sum(statistics)

        text = (
            f'📈 Общий доход:      {total.revenue:.0f}₽\n'
            f'💰 Чистая прибыль:  {total.profit:.0f}₽\n'
            f'📉 Потери:                 {total.losses:.0f}₽\n'
            f'🎯 Маржинальность: {total.margin:.1f}%\n'
            # f'🚚 Средняя загрузка курьеров: {sum(len(c.orders) for c in self.sim.couriers) / self.sim.couriers_cnt:.1f}'
        )
        self.results_label.setText(text)

    def show_day_details(self, day_idx):
        if self.sim and 0 <= day_idx < len(self.statistics):
            self.details_tab.update_day_details(self.statistics[day_idx])
