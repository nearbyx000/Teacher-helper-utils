import socket
import mss
import cv2
import numpy as np
import signal
import sys

HOST = '0.0.0.0'  # Сервер слушает все интерфейсы
PORT = 5000

def start_server():
    server_socket = None
    conn = None
    try:
        # Создаем сокет
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"Сервер запущен, ждет подключений на {HOST}:{PORT}")

        # Принимаем подключение
        conn, addr = server_socket.accept()
        print(f"Подключен клиент: {addr}")

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Захват основного монитора

            while True:
                # Захват экрана
                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # Изменение размера до 400x400
                frame = cv2.resize(frame, (400, 400))

                # Кодирование кадра в JPEG
                _, encoded_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                data = encoded_frame.tobytes()

                # Отправка размера данных и самих данных
                conn.sendall(len(data).to_bytes(4, 'big'))  # Отправляем размер данных
                conn.sendall(data)  # Отправляем сами данные

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        # Закрываем соединение и сокет
        if conn:
            conn.close()
        if server_socket:
            server_socket.close()
        print("Сервер остановлен.")

def signal_handler(sig, frame):
    """Обработчик сигнала для корректного завершения работы"""
    print("\nСервер завершает работу...")
    sys.exit(0)

# Регистрируем обработчик сигнала SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    start_server()