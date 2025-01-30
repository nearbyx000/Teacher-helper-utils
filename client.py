import socket
import cv2
import numpy as np

SERVER_IP = '127.0.0.1'
PORT = 5000

def start_client():
    # Создаем сокет
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, PORT))
    print("Подключение к серверу...")

    while True:
        # Получаем размер кадра
        data_length = int.from_bytes(client_socket.recv(4), 'big')
        data = b''

        # Чтение данных кадра
        while len(data) < data_length:
            packet = client_socket.recv(data_length - len(data))
            if not packet:
                break
            data += packet

        # Декодирование кадра
        frame = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        # Отображение кадра
        cv2.imshow("Remote Screen", frame)
        if cv2.waitKey(1) == 27:  # Выход по нажатию ESC
            break

    client_socket.close()

if __name__ == "__main__":
    start_client()
