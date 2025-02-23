# client.py
import requests
from urllib.parse import urlparse

def find_devices_in_network(network_range="192.168.1"):
    """Сканирует сеть и находит устройства с работающим сервером."""
    devices = []
    for i in range(1, 255):
        ip = f"{network_range}.{i}"
        try:
            response = requests.get(f"http://{ip}:5000/video_feed", timeout=0.5)
            if response.status_code == 200:
                devices.append(ip)
        except requests.exceptions.RequestException:
            continue
    return devices

def get_video_stream_url(ip):
    """Возвращает URL видеопотока для устройства."""
    return f"http://{ip}:5000/video_feed"