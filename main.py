import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QStackedWidget
)
from PySide6.QtCore import Qt, QProcess
import os
from qt_material import apply_stylesheet  # Импортируем библиотеку для тем

# Функция для загрузки стилей из файла по указанному пути
def load_stylesheet(filepath):
    """
    Загружает стили из файла по указанному пути и возвращает их в виде строки.
    
    :param filepath: Полный путь к файлу стилей (например, "C:/styles/styles.qss").
    :return: Содержимое файла стилей в виде строки.
    """
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(filepath):
            print(f"Файл стилей не найден: {filepath}")
            return ""
        
        # Читаем содержимое файла
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Ошибка при загрузке стилей: {e}")
        return ""

# Список устройств в сети (заглушка)
devices = ["192.168.1.2", "192.168.1.3"]  # Замените на реальные IP-адреса

class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Заголовок
        self.label = QLabel("Список устройств в сети:")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

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
        self.search_btn.clicked.connect(self.search_devices)
        self.layout.addWidget(self.search_btn)

        # Кнопка завершения урока
        self.shutdown_btn = QPushButton("Завершить урок")
        self.shutdown_btn.setObjectName("shutdown_button")  # Устанавливаем ID для стилизации
        self.shutdown_btn.clicked.connect(self.shutdown_all)
        self.layout.addWidget(self.shutdown_btn)

        self.setLayout(self.layout)
        self.processes = []  # Список для отслеживания запущенных процессов

    def update_device_list(self):
        """Обновляет список устройств на экране"""
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        for i, device in enumerate(devices):
            btn = QPushButton(device)
            btn.setObjectName("device_button")  # Устанавливаем класс для стилизации
            btn.clicked.connect(lambda _, ip=device: self.device_selected(ip))
            self.grid_layout.addWidget(btn, i, 0)

    def search_devices(self):
        """Запускает поиск устройств и обновляет список"""
        global devices
        devices = ["192.168.1.2", "192.168.1.3"]  # Заглушка
        self.update_device_list()

        # Запуск client.py для каждого устройства
        for device_ip in devices:
            process = QProcess()
            process.start("python", ["client.py", device_ip])
            self.processes.append(process)

    def shutdown_all(self):
        """Завершает все процессы и закрывает приложение"""
        for process in self.processes:
            try:
                process.terminate()
            except Exception as e:
                print(f"Ошибка при завершении процесса: {e}")

        # Закрываем приложение
        QApplication.quit()

    def device_selected(self, device_ip):
        """Переход на экран устройства"""
        self.parent().set_current_screen("device_screen", device_ip)

class DeviceScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Заголовок
        self.device_label = QLabel("Устройство: ")
        self.device_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.device_label)

        # Кнопка "Назад"
        self.back_btn = QPushButton("Назад")
        self.back_btn.setObjectName("back_button")  # Устанавливаем ID для стилизации
        self.back_btn.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_btn)

        self.setLayout(self.layout)

    def set_device(self, device_name):
        """Устанавливает имя устройства"""
        self.device_label.setText(f"Устройство: {device_name}")

    def go_back(self):
        """Возврат на главный экран"""
        self.parent().set_current_screen("main_screen")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VNC Viewer")
        self.setGeometry(100, 100, 800, 600)

        # Применяем тему Material Design
        apply_stylesheet(self, theme='light_blue.xml')  # Вы можете выбрать другую тему

        # Создаем стек для переключения экранов
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Главный экран
        self.main_screen = MainScreen()
        self.main_screen.setParent(self)
        self.stacked_widget.addWidget(self.main_screen)

        # Экран устройства
        self.device_screen = DeviceScreen()
        self.device_screen.setParent(self)
        self.stacked_widget.addWidget(self.device_screen)

    def set_current_screen(self, screen_name, device_ip=None):
        """Переключение между экранами"""
        if screen_name == "main_screen":
            self.stacked_widget.setCurrentWidget(self.main_screen)
        elif screen_name == "device_screen":
            self.device_screen.set_device(device_ip)
            self.stacked_widget.setCurrentWidget(self.device_screen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())