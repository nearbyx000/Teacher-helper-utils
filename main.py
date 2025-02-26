import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QStackedWidget,
    QProgressBar, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont
from resources import *  # Импортируем скомпилированные ресурсы


class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Заголовок
        self.label = QLabel("Добро пожаловать!")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Roboto", 14))
        self.layout.addWidget(self.label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # Список элементов
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid = QWidget()
        self.grid_layout = QGridLayout()
        self.grid.setLayout(self.grid_layout)
        self.scroll.setWidget(self.grid)
        self.layout.addWidget(self.scroll)

        # Кнопка "Начать"
        self.start_btn = QPushButton("Начать")
        self.start_btn.setIcon(QIcon(":/icons/search_icon.png"))  # Используем иконку из ресурсов
        self.start_btn.setFont(QFont("Roboto", 12))
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.layout.addWidget(self.start_btn)

        # Кнопка "Выход"
        self.exit_btn = QPushButton("Выход")
        self.exit_btn.setIcon(QIcon(":/icons/shutdown_icon.png"))  # Используем иконку из ресурсов
        self.exit_btn.setFont(QFont("Roboto", 12))
        self.exit_btn.setObjectName("exit_button")  # Устанавливаем имя для стилизации
        self.exit_btn.clicked.connect(self.on_exit_clicked)
        self.layout.addWidget(self.exit_btn)

        self.setLayout(self.layout)

        # Добавление теней
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(Qt.gray)
        self.start_btn.setGraphicsEffect(shadow)
        self.exit_btn.setGraphicsEffect(shadow)

    def on_start_clicked(self):
        """Обработчик нажатия кнопки 'Начать'."""
        self.progress_bar.setValue(50)  # Пример изменения прогресс-бара
        self.label.setText("Процесс запущен!")

    def on_exit_clicked(self):
        """Обработчик нажатия кнопки 'Выход'."""
        QApplication.quit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Мое приложение")
        self.setGeometry(100, 100, 800, 600)

        # Загрузка стилей из ресурсов
        with open(":/styles.qss", "r") as f:
            self.setStyleSheet(f.read())

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