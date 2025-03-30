
import sys
from PyQt5.QtWidgets import QApplication

from .ui.main_window import MainWindow

    # Создание и настройка приложения
app = QApplication(sys.argv)
app.setStyle('Fusion')

# Создание и отображение главного окна
window = MainWindow()
window.show()

# Запуск основного цикла
sys.exit(app.exec_())