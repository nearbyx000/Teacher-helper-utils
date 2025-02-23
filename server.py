# server.py
import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import io

class VideoStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/video_feed':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()

            cap = cv2.VideoCapture(0)  # Захват видео с камеры
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_data = buffer.tobytes()

                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame_data))
                    self.end_headers()
                    self.wfile.write(frame_data)
                    self.wfile.write(b'\r\n')
            finally:
                cap.release()

def run_server():
    server_address = ('0.0.0.0', 5000)
    httpd = HTTPServer(server_address, VideoStreamHandler)
    print("Запуск сервера на порту 5000...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()