import sys
import subprocess
import socket
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QProgressBar,
    QGraphicsDropShadowEffect, QStackedWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont
from resources import *


class NetworkScanner(QThread):
    devices_found = Signal(list)

    def __init__(self, ip_range):
        super().__init__()
        self.ip_range = ip_range

    def run(self):
        devices = []
        for i in range(1, 255):
            ip = f"{self.ip_range}.{i}"
            try:
                socket.create_connection((ip, 5900), timeout=1)
                devices.append(ip)
            except (socket.timeout, ConnectionRefusedError):
                continue
        self.devices_found.emit(devices)


class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.label = QLabel("Добро пожаловать!")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Roboto", 14))
        self.layout.addWidget(self.label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.device_list = QListWidget()
        self.layout.addWidget(self.device_list)

        self.search_btn = QPushButton("Поиск устройств")
        self.search_btn.setIcon(QIcon(":/icons/search_icon.png"))
        self.search_btn.setFont(QFont("Roboto", 12))
        self.search_btn.clicked.connect(self.on_search_clicked)
        self.layout.addWidget(self.search_btn)

        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setIcon(QIcon(":/icons/connect_icon.png"))
        self.connect_btn.setFont(QFont("Roboto", 12))
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.layout.addWidget(self.connect_btn)

        self.exit_btn = QPushButton("Выход")
        self.exit_btn.setIcon(QIcon(":/icons/shutdown_icon.png"))
        self.exit_btn.setFont(QFont("Roboto", 12))
        self.exit_btn.setObjectName("exit_button")
        self.exit_btn.clicked.connect(self.on_exit_clicked)
        self.layout.addWidget(self.exit_btn)

        self.setLayout(self.layout)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(Qt.gray)
        self.search_btn.setGraphicsEffect(shadow)
        self.connect_btn.setGraphicsEffect(shadow)
        self.exit_btn.setGraphicsEffect(shadow)

    def on_search_clicked(self):
        self.device_list.clear()
        self.label.setText("Поиск устройств...")
        self.progress_bar.setValue(0)

        self.scanner = NetworkScanner("192.168.1")
        self.scanner.devices_found.connect(self.on_devices_found)
        self.scanner.start()

    def on_devices_found(self, devices):
        if devices:
            self.device_list.addItems(devices)
            self.label.setText(f"Найдено устройств: {len(devices)}")
            self.progress_bar.setValue(100)
        else:
            QMessageBox.warning(self, "Ошибка", "Устройства не найдены.")
            self.label.setText("Устройства не найдены.")
            self.progress_bar.setValue(0)

    def on_connect_clicked(self):
        selected_device = self.device_list.currentItem()
        if selected_device:
            ip = selected_device.text()
            try:
                subprocess.Popen(["vncviewer.exe", ip])
                self.label.setText(f"Подключение к {ip}...")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться: {e}")
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите устройство из списка.")

    def on_exit_clicked(self):
        QApplication.quit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление TigerVNC")
        self.setGeometry(100, 100, 800, 600)

        try:
            with open("styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Файл styles.qss не найден. Убедитесь, что он находится в той же директории, что и main.py.")

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.main_screen = MainScreen()
        self.stacked_widget.addWidget(self.main_screen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```