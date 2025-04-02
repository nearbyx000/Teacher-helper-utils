import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import threading
from PIL import Image, ImageTk
import numpy as np

class VideoStreamWindow:
    def __init__(self, master, student_ip):
        self.master = master
        self.student_ip = student_ip
        self.width, self.height = 1280, 720  # Стандартное разрешение
        
        self.window = tk.Toplevel(master)
        self.window.title(f"Экран ученика {student_ip}")
        
        self.label = tk.Label(self.window)
        self.label.pack()
        
        self.process = None
        self.running = False
        self.start_stream()

    def start_stream(self):
        """Запуск FFmpeg для получения потока"""
        self.running = True
        command = [
            'ffmpeg',
            '-i', f'rtmp://{self.student_ip}/live/stream',
            '-f', 'image2pipe',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo',
            '-loglevel', 'quiet',
            '-'
        ]
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)
        self.update_frame()

    def update_frame(self):
        if not self.running:
            return
            
        try:
            raw_frame = self.process.stdout.read(self.width * self.height * 3)
            if raw_frame:
                frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((self.height, self.width, 3))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label.imgtk = imgtk
                self.label.config(image=imgtk)
        except Exception as e:
            print(f"Ошибка видео: {e}")
            
        self.window.after(10, self.update_frame)

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()

class MainApplication:
    def __init__(self, master):
        self.master = master
        master.title("Мониторинг класса")
        master.geometry("400x200")
        
        self.active_streams = {}  # {ip: VideoStreamWindow}
        
        # GUI элементы
        self.btn_discover = tk.Button(master, text="Найти учеников", command=self.discover_students)
        self.btn_discover.pack(pady=20)
        
        self.status_label = tk.Label(master, text="Готов к работе")
        self.status_label.pack()

    def discover_students(self):
        """Запуск поиска учеников"""
        self.status_label.config(text="Поиск учеников...")
        self.btn_discover.config(state=tk.DISABLED)
        
        threading.Thread(target=self._run_discovery, daemon=True).start()

    def _run_discovery(self):
        """Запуск внешнего скрипта и обработка результатов"""
        try:
            result = subprocess.run(
                ['python3', 'student_discovery.py'],
                capture_output=True,
                text=True,
                check=True
            )
            
            students = json.loads(result.stdout)
            self.master.after(0, self._process_discovery_results, students)
            
        except Exception as e:
            self.master.after(0, self._discovery_failed, str(e))

    def _process_discovery_results(self, student_ips):
        """Обработка найденных учеников"""
        for ip in student_ips:
            if ip not in self.active_streams:
                self.active_streams[ip] = VideoStreamWindow(self.master, ip)
                
        self.status_label.config(text=f"Найдено учеников: {len(student_ips)}")
        self.btn_discover.config(state=tk.NORMAL)

    def _discovery_failed(self, error):
        """Обработка ошибок поиска"""
        messagebox.showerror("Ошибка", f"Не удалось найти учеников:\n{error}")
        self.status_label.config(text="Ошибка поиска")
        self.btn_discover.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()