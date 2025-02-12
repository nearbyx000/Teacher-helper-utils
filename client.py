import socket
import cv2
import numpy as np

def start_client(server_ip):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, 5000))

    while True:
        # Получаем размер данных
        data_size = int.from_bytes(client_socket.recv(4), 'big')
        
        # Получаем сами данные
        data = b''
        while len(data) < data_size:
            packet = client_socket.recv(data_size - len(data))
            if not packet:
                break
            data += packet

        # Декодируем кадр
        frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        
        # Отображаем кадр
        cv2.imshow(f"Экран устройства {server_ip}", frame)
        
        # Выход по нажатию 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    client_socket.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_client("IP_АДРЕС_СЕРВЕРА")  # Замените на IP-адрес сервера