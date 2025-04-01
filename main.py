import subprocess
import numpy as np
import cv2
import tkinter as tk
from PIL import Image, ImageTk

class X11Stream:
    def __init__(self, master):
        self.master = master
        self.master.title("FFmpeg X11 Stream")
        
        # Разрешение экрана (замените на ваше!)
        self.width, self.height = 1920, 1080
        
        # Запуск FFmpeg
        self.process = self.start_ffmpeg()
        
        # GUI элементы
        self.label = tk.Label(master)
        self.label.pack()
        
        # Запуск обновления кадров
        self.update_frame()

    def start_ffmpeg(self):
        """Запускает FFmpeg для захвата X11 экрана."""
        command = [
            'ffmpeg',
            '-f', 'x11grab',      # Используем X11
            '-i', ':0.0',         # Захват всего экрана
            '-f', 'image2pipe',   # Вывод в pipe
            '-pix_fmt', 'rgb24',  # Формат пикселей
            '-vcodec', 'rawvideo',# Без сжатия
            '-loglevel', 'quiet', # Отключаем логи
            '-'                   # Вывод в stdout
        ]
        return subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)

    def update_frame(self):
        """Обновляет кадр в GUI."""
        # Чтение сырых данных кадра
        raw_frame = self.process.stdout.read(self.width * self.height * 3)
        if not raw_frame:
            return
            
        # Конвертация в numpy array
        frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((self.height, self.width, 3))
        
        # Конвертация для Tkinter
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Обновление GUI
        self.label.imgtk = imgtk
        self.label.config(image=imgtk)
        
        # Повтор через 10 мс (~100 FPS)
        self.master.after(10, self.update_frame)

    def stop(self):
        """Остановка потока."""
        self.process.terminate()

if __name__ == "__main__":
    root = tk.Tk()
    app = X11Stream(root)
    root.protocol("WM_DELETE_WINDOW", app.stop)
    root.mainloop()