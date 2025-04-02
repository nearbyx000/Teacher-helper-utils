import subprocess
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from Xlib import display
import time

class X11Stream:
    def __init__(self, master):
        self.master = master
        self.master.title("FFmpeg X11 Stream")
        
        # Автоматическое определение разрешения
        self.width, self.height = self.get_screen_resolution()
        
        # Запуск FFmpeg
        self.process = self.start_ffmpeg()
        if not self.process:
            return
            
        # GUI элементы
        self.label = tk.Label(master)
        self.label.pack()
        
        self.update_frame()

    def get_screen_resolution(self):
        d = display.Display().screen().root
        return d.get_geometry().width, d.get_geometry().height

    def start_ffmpeg(self):
        try:
            return subprocess.Popen([
                'ffmpeg',
                '-f', 'x11grab',
                '-i', ':0.0',
                '-f', 'image2pipe',
                '-pix_fmt', 'rgb24',
                '-vcodec', 'rawvideo',
                '-loglevel', 'quiet',
                '-'
            ], stdout=subprocess.PIPE, bufsize=10**8)
        except FileNotFoundError:
            print("Ошибка: Установите FFmpeg!")
            return None

    def update_frame(self):
        start_time = time.time()
        
        # Чтение кадра
        raw_frame = self.process.stdout.read(self.width * self.height * 3)
        if len(raw_frame) != self.width * self.height * 3:
            print("Ошибка: Неверный размер кадра!")
            return
            
        # Конвертация
        frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((self.height, self.width, 3))
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Обновление GUI
        self.label.imgtk = imgtk
        self.label.config(image=imgtk)
        
        # Динамическая задержка
        processing_time = (time.time() - start_time) * 1000  # ms
        delay = max(1, int(10 - processing_time))
        self.master.after(delay, self.update_frame)

    def stop(self):
        if self.process:
            self.process.terminate()

if __name__ == "__main__":
    root = tk.Tk()
    app = X11Stream(root)
    root.protocol("WM_DELETE_WINDOW", app.stop)
    root.mainloop()