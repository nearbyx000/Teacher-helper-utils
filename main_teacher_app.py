import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import threading
import socket
import os
import time # Добавлен импорт time для задержки в потоке объявления IP
from PIL import Image, ImageTk # Для работы с изображениями в Tkinter
import numpy as np # Для преобразования байтов в массив numpy для Pillow

# ВНИМАНИЕ: Убедитесь, что файлы main.py, students_discover.py
# и student_stream_daemon.py находятся в той же директории,
# что и teacher_master_app.py, или укажите полные пути к ним.
# ВНИМАНИЕ: Убедитесь, что файлы main.py, students_discover.py
# и student_stream_daemon.py находятся в той же директории,
# что и teacher_master_app.py, или укажите полные пути к ним.

# Класс для отображения видеопотока ученика
class VideoStreamWindow:
    def __init__(self, master, student_ip, teacher_ip):
        self.master = master
        self.student_ip = student_ip
        self.teacher_ip = teacher_ip
        self.width, self.height = 1280, 720  # Стандартное разрешение, можно сделать настраиваемым
        self.process = None
        self.running = False

        self.window = tk.Toplevel(master)
        self.window.title(f"Экран ученика {student_ip}")
        self.window.protocol("WM_DELETE_WINDOW", self.stop) # Добавлено для корректного закрытия окна

        self.label = tk.Label(self.window)
        self.label.pack()

        self.start_stream()

    def start_stream(self):
        """
        Запуск FFmpeg для получения потока от ученика.
        Поток будет приходить на RTMP-сервер, запущенный на IP учителя.
        """
        self.running = True
        stream_name = f"student_{self.student_ip.replace('.', '_')}"

        command = [
            'ffmpeg',
            '-i', f'rtmp://{self.teacher_ip}/live/{stream_name}', # Читаем с RTMP-сервера учителя
            '-f', 'image2pipe',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo',
            '-loglevel', 'quiet',
            '-'
        ]
        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)
            self.update_frame()
        except FileNotFoundError:
            messagebox.showerror("Ошибка FFmpeg", "FFmpeg не найден. Убедитесь, что он установлен и доступен в PATH.")
            self.stop()
        except Exception as e:
            messagebox.showerror("Ошибка запуска потока", f"Не удалось запустить поток для {self.student_ip}: {e}")
            self.stop()

    def update_frame(self):
        """Обновляет кадр видеопотока в окне."""
        if not self.running: # Если поток остановлен, прекращаем обновления
            return

        # Проверяем, не завершился ли процесс FFmpeg
        if self.process and self.process.poll() is not None:
            if self.running: # Если процесс завершился, но мы еще пытались обновлять
                print(f"FFmpeg процесс для {self.student_ip} завершился. Код: {self.process.poll()}")
            self.stop()
            return

        try:
            # Читаем данные из stdout FFmpeg. Размер должен соответствовать self.width * self.height * 3.
            raw_frame = self.process.stdout.read(self.width * self.height * 3)
            if raw_frame:
                # Преобразуем байты в массив numpy и затем в изображение PIL
                frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((self.height, self.width, 3))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label.imgtk = imgtk # Важно сохранить ссылку, чтобы изображение не было удалено сборщиком мусора
                self.label.config(image=imgtk)
            else:
                # Если raw_frame пуст, это может указывать на конец потока или ошибку
                print(f"Пустой кадр для {self.student_ip}. Возможно, поток завершился.")
                self.stop()
                return

        except ValueError as ve:
            print(f"Ошибка размера кадра для {self.student_ip}: {ve}. Возможно, разрешение потока изменилось или не соответствует.")
            self.stop()
            return
        except Exception as e:
            print(f"Ошибка видеопотока для {self.student_ip}: {e}")
            self.stop()
            return

        self.window.after(10, self.update_frame) # Продолжаем обновлять кадр каждые 10 мс

    def stop(self):
        """Останавливает видеопоток и закрывает окно."""
        self.running = False
        if self.process:
            self.process.terminate() # Пытаемся корректно завершить процесс
            try:
                self.process.wait(timeout=2) # Ждем до 2 секунд, пока процесс завершится
            except subprocess.TimeoutExpired:
                print(f"FFmpeg процесс для {self.student_ip} не завершился, принудительно убиваю.")
                self.process.kill() # Если не завершился, убиваем принудительно
            self.process = None # Очищаем ссылку на процесс
            print(f"Поток для {self.student_ip} остановлен.")
        if self.window.winfo_exists():
            self.window.destroy()

# Основное приложение для учителя
class MainApplication:
    def __init__(self, master):
        self.master = master
        master.title("Мониторинг класса")
        master.geometry("400x250")

        self.active_streams = {}

        self.teacher_ip = self.get_local_ip()
        if self.teacher_ip:
            tk.Label(master, text=f"Ваш IP-адрес (для учеников): {self.teacher_ip}").pack(pady=5)
            # Запускаем широковещательное объявление IP учителя
            threading.Thread(target=self._start_teacher_announcer, daemon=True).start()
        else:
            tk.Label(master, text="Не удалось определить ваш IP-адрес.").pack(pady=5)
            messagebox.showwarning("Предупреждение", "Не удалось определить ваш локальный IP-адрес. Убедитесь, что сетевые настройки корректны.")

        self.btn_discover = tk.Button(master, text="Найти учеников", command=self.discover_students)
        self.btn_discover.pack(pady=10)

        self.status_label = tk.Label(master, text="Готов к работе")
        self.status_label.pack(pady=5)

    def get_local_ip(self):
        """Автоматически определяет локальный IP-адрес учителя."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80)) # Подключение к внешнему адресу, чтобы получить локальный IP
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"Ошибка при определении IP-адреса: {e}")
            return None

    def _start_teacher_announcer(self):
        """Широковещательно объявляет IP-адрес учителя, чтобы ученики могли его найти."""
        if not self.teacher_ip:
            return

        # Использование UDP-сокета для широковещания
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Отправляем на порт 5000, который будет слушать student_stream_daemon.py
        server_address = ('255.255.255.255', 5000) # Широковещательный адрес и порт

        print(f"Начинаю широковещательное объявление IP: {self.teacher_ip}")
        while True:
            try:
                # Отправляем IP учителя, чтобы student_stream_daemon.py мог его получить
                message = f"TEACHER_IP:{self.teacher_ip}".encode('utf-8')
                sock.sendto(message, server_address)
                time.sleep(5) # Объявляем IP каждые 5 секунд
            except Exception as e:
                print(f"Ошибка при широковещательном объявлении: {e}")
                time.sleep(5) # Ждем перед следующей попыткой

    def discover_students(self):
        """Запускает students_discover.py для поиска учеников."""
        if not os.path.exists('students_discover.py'):
            messagebox.showerror("Ошибка", "Файл students_discover.py не найден в текущей директории.")
            return

        self.status_label.config(text="Поиск учеников...")
        self.btn_discover.config(state=tk.DISABLED)

        threading.Thread(target=self._run_discovery_script, daemon=True).start()

    def _run_discovery_script(self):
        """Выполняет students_discover.py и обрабатывает его вывод."""
        try:
            result = subprocess.run(
                ['python3', 'students_discover.py'],
                capture_output=True,
                text=True,
                check=True
            )

            # Ожидаем, что students_discover.py выведет JSON-строку с IP-адресами
            student_ips = json.loads(result.stdout)
            self.master.after(0, self._process_discovery_results, student_ips)

        except FileNotFoundError:
            self.master.after(0, self._discovery_failed, "Исполняемый файл 'python3' или 'students_discover.py' не найден. Убедитесь в их наличии и корректности PATH.")
        except subprocess.CalledProcessError as e:
            self.master.after(0, self._discovery_failed, f"Ошибка при выполнении students_discover.py:\n{e.stderr}")
        except json.JSONDecodeError:
            self.master.after(0, self._discovery_failed, f"Некорректный JSON-ответ от students_discover.py:\n{result.stdout}")
        except Exception as e:
            self.master.after(0, self._discovery_failed, f"Неизвестная ошибка при поиске учеников: {e}")

    def _process_discovery_results(self, student_ips):
        """Обрабатывает найденные IP-адреса учеников, открывая/закрывая окна потоков."""
        current_active_ips = set(self.active_streams.keys())
        discovered_ips = set(student_ips)

        # Открываем окна для новых учеников
        for ip in discovered_ips - current_active_ips:
            print(f"Найдена новый ученик: {ip}. Открываю окно потока.")
            # Передаем IP учителя, чтобы ученик знал, куда стримить
            self.active_streams[ip] = VideoStreamWindow(self.master, ip, self.teacher_ip)

        # Закрываем окна для учеников, которые больше не обнаружены
        for ip in current_active_ips - discovered_ips:
            if ip in self.active_streams:
                print(f"Ученик {ip} больше не обнаружен. Закрываю окно потока.")
                self.active_streams[ip].stop()
                del self.active_streams[ip]

        self.status_label.config(text=f"Найдено учеников: {len(discovered_ips)}")
        self.btn_discover.config(state=tk.NORMAL)

    def _discovery_failed(self, error):
        """Отображает сообщение об ошибке при поиске учеников."""
        messagebox.showerror("Ошибка", f"Не удалось найти учеников:\n{error}")
        self.status_label.config(text="Ошибка поиска")
        self.btn_discover.config(state=tk.NORMAL)

    def on_closing(self):
        """Функция, вызываемая при закрытии главного окна."""
        print("Закрытие главного приложения. Останавливаю все потоки.")
        for ip, stream_window in list(self.active_streams.items()):
            stream_window.stop()
        self.master.destroy()

if __name__ == "__main__":
    # Проверка наличия необходимых скриптов
    required_scripts = ['students_discover.py']
    for script in required_scripts:
        if not os.path.exists(script):
            print(f"Ошибка: Необходимый скрипт '{script}' не найден в текущей директории.")
            print("Убедитесь, что все скрипты находятся рядом с teacher_master_app.py.")
            exit(1)

    # Проверка наличия FFmpeg в PATH
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True, text=True)
        print("FFmpeg найден в PATH.")
    except FileNotFoundError:
        print("Ошибка: FFmpeg не найден в PATH. Пожалуйста, установите FFmpeg и добавьте его в системную переменную PATH.")
        exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при проверке FFmpeg: {e.stderr}")
        exit(1)

    root = tk.Tk()
    app = MainApplication(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()