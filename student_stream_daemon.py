import subprocess
import time

def start_stream():
    while True:
        try:
            # Захват экрана через FFmpeg и отправка на сервер
            cmd = [
                "ffmpeg",
                "-f", "x11grab", "-i", ":0.0",  # Захват экрана (Linux)
                "-f", "pulse", "-i", "default",  # Захват звука (опционально)
                "-c:v", "libx264", "-preset", "ultrafast",
                "-f", "flv", "rtmp://SERVER_IP/live/student_1"
            ]
            subprocess.run(cmd)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)  # Перезапуск через 5 сек

if __name__ == "__main__":
    start_stream()