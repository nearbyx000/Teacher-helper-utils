import socket
import mss
import cv2
import numpy as np

HOST = '0.0.0.0'  # Сервер слушает все интерфейсы
PORT = 5000

def start_server():
    # Создаем сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Сервер запущен, ждет подключений на {HOST}:{PORT}")

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

    conn.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()