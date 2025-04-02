import socket
import json
import sys

def discover_students():
    """Поиск учеников в сети через UDP"""
    students = []
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", 5000))
        sock.settimeout(2.0)

        # Отправка запроса
        sock.sendto(b"DISCOVER_STUDENTS", ("255.255.255.255", 5000))

        # Получение ответов
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if data == b"STUDENT_HERE":
                    students.append(addr[0])
            except socket.timeout:
                break
                
    except Exception as e:
        print(f"Ошибка при поиске: {e}", file=sys.stderr)
    
    return students

if __name__ == "__main__":
    # При запуске скрипта возвращаем JSON с найденными учениками
    print(json.dumps(discover_students()))