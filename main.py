import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QStackedWidget,
    QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from qt_material import apply_stylesheet
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor


class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Создаем новый цикл событий
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Заголовок
        self.label = QLabel("Список устройств в сети:")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 254)  # Диапазон IP-адресов
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # Список устройств
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid = QWidget()
        self.grid_layout = QGridLayout()
        self.grid.setLayout(self.grid_layout)
        self.scroll.setWidget(self.grid)
        self.layout.addWidget(self.scroll)

        # Кнопка поиска устройств
        self.search_btn = QPushButton("Поиск устройств")
        self.search_btn.clicked.connect(self.start_device_search)
        self.layout.addWidget(self.search_btn)

        # Кнопка завершения урока
        self.shutdown_btn = QPushButton("Завершить урок")
        self.shutdown_btn.setObjectName("shutdown_button")
        self.shutdown_btn.clicked.connect(self.shutdown_all)
        self.layout.addWidget(self.shutdown_btn)

        self.setLayout(self.layout)
        self.device_widgets = []  # Список для хранения виджетов устройств

    def start_device_search(self):
        """Запускает асинхронный поиск устройств"""
        self.search_btn.setEnabled(False)  # Отключаем кнопку во время сканирования
        self.progress_bar.setValue(0)  # Сбрасываем прогресс-бар
        network_range = "192.168.1"  # Укажите диапазон сети

        # Запускаем асинхронный процесс
        asyncio.run_coroutine_threadsafe(self.find_devices_in_network(network_range), self.loop)

    async def find_devices_in_network(self, network_range):
        """Асинхронно сканирует сеть и находит устройства с работающим сервером."""
        devices = []
        with ThreadPoolExecutor() as executor:
            tasks = [
                self.loop.run_in_executor(executor, self.check_device, f"{network_range}.{i}")
                for i in range(1, 255)
            ]
            for i, task in enumerate(asyncio.as_completed(tasks), start=1):
                ip = await task
                if ip:
                    devices.append(ip)
                self.progress_bar.setValue(i)  # Обновляем прогресс-бар

        self.update_device_list(devices)
        self.search_btn.setEnabled(True)  # Включаем кнопку после завершения

    def check_device(self, ip):
        """Проверяет доступность устройства."""
        try:
            response = requests.get(f"http://{ip}:5000/video_feed", timeout=0.5)
            if response.status_code == 200:
                return ip
        except requests.exceptions.RequestException:
            pass
        return None

    def update_device_list(self, devices):
        """Обновляет список устройств на экране"""
        for widget, _ in self.device_widgets:
            widget.setParent(None)
        self.device_widgets.clear()

        for i, device in enumerate(devices):
            video_widget = QLabel()
            video_widget.setFixedSize(400, 400)
            video_widget.setStyleSheet("border: 1px solid black;")
            self.grid_layout.addWidget(video_widget, i // 3, i % 3)

            # Запускаем таймер для обновления видеопотока
            timer = QTimer()
            timer.timeout.connect(lambda ip=device, widget=video_widget: self.update_video_frame(ip, widget))
            timer.start(100)  # Обновление каждые 100 мс
            self.device_widgets.append((video_widget, timer))

    def update_video_frame(self, ip, widget):
        """Обновляет кадр видеопотока"""
        try:
            response = requests.get(f"http://{ip}:5000/video_feed", stream=True, timeout=0.5)
            if response.status_code == 200:
                data = response.raw.read()
                image = QImage.fromData(data)
                pixmap = QPixmap.fromImage(image)
                widget.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))
        except requests.exceptions.RequestException:
            pass

    def shutdown_all(self):
        """Завершает все процессы и закрывает приложение"""
        for _, timer in self.device_widgets:
            timer.stop()
        QApplication.quit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VNC Viewer")
        self.setGeometry(100, 100, 800, 600)

        # Применяем тему Material Design
        apply_stylesheet(self, theme='light_blue.xml')

        # Создаем стек для переключения экранов
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Главный экран
        self.main_screen = MainScreen()
        self.stacked_widget.addWidget(self.main_screen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())    