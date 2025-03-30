from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

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
