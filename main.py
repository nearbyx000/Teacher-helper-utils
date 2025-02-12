from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.clock import Clock
import sqlite3
import hashlib

# Создаем подключение к базе данных
class Database:
    def __init__(self, db_name='users.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             username TEXT UNIQUE NOT NULL,
                             password TEXT NOT NULL)''')
        self.conn.commit()
        
        # Добавляем тестового пользователя
        if not self.check_user_exists('admin'):
            self.add_user('admin', 'admin123')

    def add_user(self, username, password):
        hashed_password = self.hash_password(password)
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                              (username, hashed_password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def check_user_exists(self, username):
        self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        return self.cursor.fetchone() is not None

    def check_login(self, username, password):
        hashed_password = self.hash_password(password)
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", 
                          (username, hashed_password))
        return self.cursor.fetchone() is not None

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def __del__(self):
        self.conn.close()

# Экран авторизации
class LoginScreen(Screen):
    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text
        
        db = Database()
        if db.check_login(username, password):
            self.manager.current = 'success'
        else:
            self.ids.error_label.text = "Invalid username or password!"
        
    def clear_fields(self):
        self.ids.username.text = ""
        self.ids.password.text = ""
        self.ids.error_label.text = ""

# Экран успешной авторизации
class SuccessScreen(Screen):
    pass

# Менеджер экранов
class ScreenManagement(ScreenManager):
    pass

# Загрузка KV разметки
Builder.load_string('''
<ScreenManagement>:
    LoginScreen:
        name: 'login'
    SuccessScreen:
        name: 'success'

<LoginScreen>:
    id: login_screen
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 15
        
        Label:
            text: 'Authorization'
            font_size: 32
            
        TextInput:
            id: username
            hint_text: 'Username'
            size_hint_y: None
            height: 40
            
        TextInput:
            id: password
            hint_text: 'Password'
            password: True
            size_hint_y: None
            height: 40
            
        Label:
            id: error_label
            text: ''
            color: (1, 0, 0, 1)
            size_hint_y: None
            height: 30
            
        Button:
            text: 'Login'
            size_hint_y: None
            height: 40
            on_release:
                root.login()
                
        Button:
            text: 'Clear'
            size_hint_y: None
            height: 40
            on_release: 
                root.clear_fields()

<SuccessScreen>:
    BoxLayout:
        orientation: 'vertical'
        
        Label:
            text: 'Login Successful!'
            font_size: 32
            
        Button:
            text: 'Logout'
            size_hint_y: None
            height: 40
            on_release: 
                app.root.current = 'login'
''')

class AuthApp(App):
    def build(self):
        return ScreenManagement()

if __name__ == '__main__':
    AuthApp().run()