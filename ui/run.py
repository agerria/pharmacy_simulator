# __package__ = 'ui'

import sys
from PyQt5.QtWidgets import QApplication

from .main_window import MainWindow

app = QApplication(sys.argv)
app.setStyle('Fusion')

window = MainWindow()
window.show()

sys.exit(app.exec_())