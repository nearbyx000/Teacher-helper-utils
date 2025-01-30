import socket
import mss
import cv2
import numpy as np

HOST = '127.0.0.1'  # Сервер слушает все интерфейсы
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

            # Кодирование и отправка кадра
            _, encoded_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            data = encoded_frame.tobytes()
            conn.sendall(len(data).to_bytes(4, 'big') + data)

    conn.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()
