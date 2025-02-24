import cv2
import socket
import numpy as np
import threading
import time

HOST = '0.0.0.0'  # Сервер слушает все интерфейсы
PORT = 5000

def capture_and_send(conn):
    cap = cv2.VideoCapture(0)  # Захват с экрана (или камеры)
    if not cap.isOpened():
        print("Ошибка: Не удалось захватить видео.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Изменение размера кадра
            frame = cv2.resize(frame, (640, 480))

            # Кодирование кадра в JPEG
            _, encoded_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            data = encoded_frame.tobytes()

            # Отправка размера данных и самих данных
            conn.sendall(len(data).to_bytes(4, 'big'))  # Отправляем размер данных
            conn.sendall(data)  # Отправляем сами данные

            time.sleep(0.03)  # Ограничение FPS (примерно 30 кадров в секунду)
    finally:
        cap.release()
        conn.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Сервер запущен, ждет подключений на {HOST}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        print(f"Подключен клиент: {addr}")
        threading.Thread(target=capture_and_send, args=(conn,)).start()

if __name__ == "__main__":
    start_server()