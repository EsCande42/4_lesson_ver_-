from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import main
import asyncio

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('GPT Telegram Bot is running!'.encode())
        return

    def do_POST(self):
        # Получаем данные от Telegram Webhook
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # Здесь можно добавить обработку webhook данных
            # Пока просто возвращаем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'ok'}
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
        return

# Для локального тестирования
if __name__ == "__main__":
    asyncio.run(main()) 