import socket
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import cookies

CHAT_SERVER_HOST = 'localhost'
CHAT_SERVER_PORT = 8547
WEB_SERVER_PORT = 8000

class ChatWebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'rb') as file:
                self.wfile.write(file.read())
        elif self.path.startswith('/api/messages'):
            self.handle_get_messages()
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == '/api/messages':
            self.handle_post_message()
        elif self.path == '/api/login':
            self.handle_login()
        elif self.path == '/api/logout':
            self.handle_logout()
        else:
            self.send_error(404, "API endpoint not found")

    def handle_get_messages(self):
        messages = ""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
                s.sendall(b'GET_MESSAGES')

                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    messages += chunk.decode()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"messages": messages.splitlines()}).encode())
        except Exception as e:
            print(f"Error in handle_get_messages: {e}")
            self.send_error(500, f"Failed to retrieve messages: {e}")

    def handle_post_message(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        message = data['message']
        nickname = data.get('nickname', 'Anonymous') 

        if not nickname:
            self.send_error(401, "Unauthorized: No nickname provided")
            return

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
                full_message = f'SEND_MESSAGE {nickname}: {message}'
                s.sendall(full_message.encode())
                print("Message sent successfully")
            self.send_response(201)
            self.end_headers()
        except Exception as e:
            print(f"Error in handle_post_message: {e}")
            self.send_error(500, f"Failed to send message: {e}")

    def handle_login(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        nickname = data.get('nickname', 'Anonymous')

        c = cookies.SimpleCookie()
        c['nickname'] = nickname
        c['nickname']['httponly'] = True
        self.send_response(200)
        self.send_header('Set-Cookie', c.output(header='', sep=''))
        self.end_headers()

    def handle_logout(self):
        self.send_response(200)
        self.send_header('Set-Cookie', 'nickname=; Max-Age=0')
        self.end_headers()

def run_server():
    server_address = ('', WEB_SERVER_PORT)
    httpd = HTTPServer(server_address, ChatWebServer)
    print(f'Starting web server on port {WEB_SERVER_PORT}')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
