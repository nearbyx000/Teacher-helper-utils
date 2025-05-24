import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import threading
import socket # Для определения IP-адреса учителя
import os     # Для проверки существования файлов скриптов

# ВНИМАНИЕ: Убедитесь, что файлы main.py, students_discover.py
# и student_stream_daemon.py находятся в той же директории,
# что и teacher_master_app.py, или укажите полные пути к ним.

# Класс для отображения видеопотока ученика
class VideoStreamWindow:
    def __init__(self, master, student_ip, teacher_ip):
        self.master = master
        self.student_ip = student_ip
        self.teacher_ip = teacher_ip # IP-адрес учителя, чтобы FFmpeg ученика знал, куда стримить
        self.width, self.height = 1280, 720  # Стандартное разрешение

        self.window = tk.Toplevel(master)
        self.window.title(f"Экран ученика {student_ip}")

        self.label = tk.Label(self.window)
        self.label.pack()

        self.process = None
        self.running = False
        self.start_stream()

    def start_stream(self):
        """
        Запуск FFmpeg для получения потока от ученика.
        Поток будет приходить на RTMP-сервер, запущенный на IP учителя.
        """
        self.running = True
        # Команда FFmpeg для чтения RTMP-потока.
        # Ученик должен стримить на rtmp://<IP_УЧИТЕЛЯ>/live/stream
        # Здесь мы читаем с rtmp://<IP_УЧЕНИКА>/live/stream, что неверно, если RTMP-сервер у учителя.
        # Если RTMP-сервер на машине учителя, то имя потока должно быть уникальным для каждого ученика.
        # Пусть будет "student_IP_ученика"
        stream_name = f"student_{self.student_ip.replace('.', '_')}" # Уникальное имя потока для каждого ученика

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
            # Убедитесь, что FFmpeg установлен и доступен в PATH
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)
            # Необходимо также убедиться, что FFmpeg запущен на стороне ученика и стримит на teacher_ip
            self.update_frame()
        except FileNotFoundError:
            messagebox.showerror("Ошибка FFmpeg", "FFmpeg не найден. Убедитесь, что он установлен и доступен в PATH.")
            self.stop() # Останавливаем поток, если FFmpeg не найден
        except Exception as e:
            messagebox.showerror("Ошибка запуска потока", f"Не удалось запустить поток для {self.student_ip}: {e}")
            self.stop()

    def update_frame(self):
        if not self.running or self.process.poll() is not None: # Проверяем, не завершился ли процесс
            if self.running: # Если процесс завершился, но мы еще пытались обновлять
                print(f"FFmpeg процесс для {self.student_ip} завершился. Код: {self.process.poll()}")
            self.stop()
            return

        try:
            # Важно: размер кадра должен соответствовать размеру потока.
            # Если разрешение ученика отличается, нужно его определить или передать.
            # Пока используем стандартное.
            raw_frame = self.process.stdout.read(self.width * self.height * 3)
            if raw_frame:
                frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((self.height, self.width, 3))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label.imgtk = imgtk
                self.label.config(image=imgtk)
        except ValueError as ve:
            print(f"Ошибка размера кадра для {self.student_ip}: {ve}. Возможно, разрешение потока изменилось или не соответствует.")
            self.stop()
            return
        except Exception as e:
            print(f"Ошибка видеопотока для {self.student_ip}: {e}")
            self.stop()
            return # Прекращаем дальнейшие обновления

        self.window.after(10, self.update_frame)

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=2) # Дать время процессу завершиться
            if self.process.poll() is None: # Если процесс все еще запущен после terminate
                self.process.kill() # Принудительно убить
            print(f"Поток для {self.student_ip} остановлен.")
        if self.window.winfo_exists(): # Проверяем, существует ли окно перед уничтожением
            self.window.destroy() # Закрываем окно при остановке

# Основное приложение для учителя
class MainApplication:
    def __init__(self, master):
        self.master = master
        master.title("Мониторинг класса")
        master.geometry("400x250") # Увеличиваем размер для IP-адреса

        self.active_streams = {}  # {ip: VideoStreamWindow}

        # Определяем IP-адрес учителя
        self.teacher_ip = self.get_local_ip()
        if self.teacher_ip:
            tk.Label(master, text=f"Ваш IP-адрес (для учеников): {self.teacher_ip}").pack(pady=5)
            # Запускаем широковещательное объявление IP учителя
            threading.Thread(target=self._start_teacher_announcer, daemon=True).start()
        else:
            tk.Label(master, text="Не удалось определить ваш IP-адрес.").pack(pady=5)
            messagebox.showwarning("Предупреждение", "Не удалось определить ваш локальный IP-адрес. Убедитесь, что сетевые настройки корректны.")

        # GUI элементы
        self.btn_discover = tk.Button(master, text="Найти учеников", command=self.discover_students)
        self.btn_discover.pack(pady=10)

        self.status_label = tk.Label(master, text="Готов к работе")
        self.status_label.pack(pady=5)

    def get_local_ip(self):
        """Автоматически определяет локальный IP-адрес учителя."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
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

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Отправляем на порт 5000, который слушает student_discovery.py
        server_address = ('255.255.255.255', 5000)

        print(f"Начинаю широковещательное объявление IP: {self.teacher_ip}")
        while True:
            try:
                # Отправляем сообщение, которое student_discovery.py ожидает как "DISCOVER_STUDENTS"
                # ИЛИ модифицируем student_discovery.py, чтобы он принимал IP учителя
                # В текущей логике students_discover.py, он сам отправляет DISCOVER_STUDENTS
                # и ждет STUDENT_HERE.
                # Для обнаружения IP учителя, потребуется модифицировать student_stream_daemon.py
                # и teacher_master_app.py
                # Пока оставим как есть, учитель просто объявляет себя, но это не используется student_discovery.py

                # Если бы teacher_master_app.py сам был сервером обнаружения, то здесь бы
                # он слушал запросы от учеников. Но student_discovery.py - это отдельный скрипт.

                # Для того, чтобы ученики знали IP учителя, учитель должен:
                # 1. Запустить RTMP-сервер
                # 2. Объявить свой IP. Ученик должен активно слушать это объявление.
                # Скрипт student_stream_daemon.py сейчас не слушает.
                # student_discovery.py ТОЛЬКО находит учеников, но не передает IP учителя.

                # Корректная логика:
                # Учитель запускает RTMP-сервер и широковещательно объявляет свой IP.
                # Ученик (student_stream_daemon.py) слушает широковещательные объявления,
                # находит IP учителя и начинает стримить на него.

                # В рамках вашего запроса "вызывать уже написанные скрипты",
                # _start_teacher_announcer пока не будет взаимодействовать с student_discovery.py
                # напрямую для передачи IP, но он нужен для будущей модификации student_stream_daemon.py.
                # Сейчас он просто объявляет IP, чтобы ученик мог его поймать.

                message = f"TEACHER_IP_ANNOUNCEMENT:{self.teacher_ip}".encode('utf-8')
                sock.sendto(message, server_address)
                time.sleep(5)
            except Exception as e:
                print(f"Ошибка при широковещательном объявлении: {e}")
                time.sleep(5)

    def discover_students(self):
        """Запускает student_discovery.py для поиска учеников."""
        if not os.path.exists('students_discover.py'):
            messagebox.showerror("Ошибка", "Файл students_discover.py не найден в текущей директории.")
            return

        self.status_label.config(text="Поиск учеников...")
        self.btn_discover.config(state=tk.DISABLED)

        # Вызываем students_discover.py как отдельный процесс
        threading.Thread(target=self._run_discovery_script, daemon=True).start()

    def _run_discovery_script(self):
        """Выполняет students_discover.py и обрабатывает его вывод."""
        try:
            # subprocess.run запускает скрипт и ждет его завершения
            result = subprocess.run(
                ['python3', 'students_discover.py'],
                capture_output=True,
                text=True,
                check=True # Вызовет исключение CalledProcessError, если скрипт завершится с ненулевым кодом
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
        """Обрабатывает найденные IP-адреса учеников."""
        current_active_ips = set(self.active_streams.keys())
        discovered_ips = set(student_ips)

        # Открываем окна для новых учеников
        for ip in discovered_ips - current_active_ips:
            print(f"Найдена новый ученик: {ip}. Открываю окно потока.")
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
            del self.active_streams[ip]
        self.master.destroy()

if __name__ == "__main__":
    # Проверка наличия необходимых скриптов
    required_scripts = ['students_discover.py'] # main.py и student_stream_daemon.py не вызываются здесь напрямую
    for script in required_scripts:
        if not os.path.exists(script):
            print(f"Ошибка: Необходимый скрипт '{script}' не найден в текущей директории.")
            print("Убедитесь, что все скрипты находятся рядом с teacher_master_app.py.")
            exit(1) # Завершаем работу, если скрипт не найден

    root = tk.Tk()
    app = MainApplication(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()