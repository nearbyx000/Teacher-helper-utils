from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
import subprocess
import threading

# Список устройств в сети (заглушка)
devices = ["192.168.1.2", "192.168.1.3"]  # Замените на реальные IP-адреса

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        
        self.label = Label(text="Список устройств в сети:")
        self.layout.add_widget(self.label)
        
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        
        self.update_device_list()
        
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)
        
        self.search_btn = Button(text="Поиск устройств", size_hint_y=None, height=40)
        self.search_btn.bind(on_press=self.search_devices)
        self.layout.add_widget(self.search_btn)
        
        self.add_widget(self.layout)
    
    def update_device_list(self):
        """Обновляет список устройств на экране"""
        self.grid.clear_widgets()
        for device in devices:
            btn = Button(text=device, size_hint_y=None, height=40)
            btn.bind(on_press=self.device_selected)
            self.grid.add_widget(btn)
    
    def search_devices(self, instance):
        """Запускает поиск устройств и обновляет список"""
        # Здесь можно добавить логику для поиска устройств в сети
        global devices
        devices = ["192.168.1.2", "192.168.1.3"]  # Заглушка для примера
        self.update_device_list()
        
        # Запуск client.py для каждого устройства
        for device_ip in devices:
            threading.Thread(target=self.start_client, args=(device_ip,)).start()
    
    def start_client(self, device_ip):
        """Запускает client.py для отображения экрана устройства"""
        try:
            subprocess.Popen(["python", "client.py", device_ip])
            print(f"Запущен client.py для устройства: {device_ip}")
        except Exception as e:
            print(f"Ошибка при запуске client.py: {e}")
    
    def device_selected(self, instance):
        device_name = instance.text
        self.manager.current = 'device_screen'
        self.manager.get_screen('device_screen').set_device(device_name)

class DeviceScreen(Screen):
    def __init__(self, **kwargs):
        super(DeviceScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        
        self.device_label = Label(text="Устройство: ")
        self.layout.add_widget(self.device_label)
        
        self.back_btn = Button(text="Назад")
        self.back_btn.bind(on_press=self.go_back)
        self.layout.add_widget(self.back_btn)
        
        self.add_widget(self.layout)
    
    def set_device(self, device_name):
        self.device_name = device_name
        self.device_label.text = f"Устройство: {device_name}"
    
    def go_back(self, instance):
        self.manager.current = 'main_screen'

class MyApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        
        self.main_screen = MainScreen(name='main_screen')
        self.device_screen = DeviceScreen(name='device_screen')
        
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.device_screen)
        
        return self.screen_manager

if __name__ == '__main__':
    MyApp().run()