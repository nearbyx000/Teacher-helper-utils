import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QStackedWidget,
    QProgressBar, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QIcon, QFont
from resources import *  # Импортируем скомпилированные ресурсы


class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Заголовок
        self.label = QLabel("Список устройств в сети:")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Roboto", 14))
        self.label.setStyleSheet("color: #ffffff;")  # Белый текст
        self.layout.addWidget(self.label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 254)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2e2e2e;
                color: white;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
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
        self.search_btn.setIcon(QIcon(":/icons/search_icon.png"))  # Используем иконку из ресурсов
        self.search_btn.setFont(QFont("Roboto", 12))
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #6200ea;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3700b3;
            }
            QPushButton:pressed {
                background-color: #1a0073;
            }
        """)
        self.search_btn.clicked.connect(self.start_device_search)
        self.layout.addWidget(self.search_btn)

        # Кнопка завершения урока
        self.shutdown_btn = QPushButton("Завершить урок")
        self.shutdown_btn.setIcon(QIcon(":/icons/shutdown_icon.png"))  # Используем иконку из ресурсов
        self.shutdown_btn.setFont(QFont("Roboto", 12))
        self.shutdown_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:pressed {
                background-color: #8e0000;
            }
        """)
        self.shutdown_btn.clicked.connect(self.shutdown_all)
        self.layout.addWidget(self.shutdown_btn)

        self.setLayout(self.layout)
        self.device_widgets = []

        # Добавление теней
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(Qt.gray)
        self.search_btn.setGraphicsEffect(shadow)
        self.shutdown_btn.setGraphicsEffect(shadow)

    def start_device_search(self):
        """Запускает асинхронный поиск устройств в сети."""
        self.search_btn.setEnabled(False)  # Отключаем кнопку во время поиска
        self.progress_bar.setValue(0)  # Сбрасываем прогресс-бар
        network_range = "192.168.1"  # Укажите диапазон сети

        # Запускаем асинхронный процесс
        asyncio.run_coroutine_threadsafe(self.find_devices_in_network(network_range), self.loop)

    async def find_devices_in_network(self, network_range):
        """Асинхронно сканирует сеть и находит устройства."""
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
        """Проверяет доступность устройства по IP."""
        try:
            response = requests.get(f"http://{ip}:5000/video_feed", timeout=0.5)
            if response.status_code == 200:
                return ip
        except requests.exceptions.RequestException:
            pass
        return None

    def update_device_list(self, devices):
        """Обновляет список устройств на экране."""
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
        """Обновляет кадр видеопотока."""
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
        """Завершает все процессы и закрывает приложение."""
        for _, timer in self.device_widgets:
            timer.stop()
        QApplication.quit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VNC Viewer")
        self.setGeometry(100, 100, 800, 600)

        # Применяем стили для главного окна
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
        """)

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