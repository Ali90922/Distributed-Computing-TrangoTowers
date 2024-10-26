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
        elif self.path == '/api/messages':
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
        """Retrieves the latest messages from the chat server."""
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
                    messages += chunk.decode('ascii')

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"messages": messages.splitlines()}).encode())
        except Exception as e:
            print(f"Error in handle_get_messages: {e}")
            self.send_error(500, f"Failed to retrieve messages: {e}")

    def handle_post_message(self):
        """Sends a message from the web client to the chat server."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        message = data.get('message', '')

        # Retrieve nickname from cookie if available
        nickname = "Anonymous"  # Default nickname
        if "Cookie" in self.headers:
            c = cookies.SimpleCookie(self.headers["Cookie"])
            nickname = c.get("nickname").value if "nickname" in c else nickname

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
                full_message = f'SEND_MESSAGE {nickname}: {message}'
                s.sendall(full_message.encode('ascii'))
                print(f"Message sent successfully: {full_message}")
            
            self.send_response(201)
            self.end_headers()
        except Exception as e:
            print(f"Error in handle_post_message: {e}")
            self.send_error(500, f"Failed to send message: {e}")

    def handle_login(self):
        """Logs in a user by setting a nickname cookie."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        nickname = data.get('nickname', 'Anonymous')

        # Set the nickname as a cookie
        c = cookies.SimpleCookie()
        c['nickname'] = nickname
        c['nickname']['httponly'] = True
        self.send_response(200)
        self.send_header('Set-Cookie', c.output(header='', sep=''))
        self.end_headers()

    def handle_logout(self):
        """Logs out a user by clearing the nickname cookie."""
        self.send_response(200)
        self.send_header('Set-Cookie', 'nickname=; Max-Age=0')
        self.end_headers()

def run_server():
    """Runs the web server."""
    server_address = ('', WEB_SERVER_PORT)
    httpd = HTTPServer(server_address, ChatWebServer)
    print(f'Starting web server on port {WEB_SERVER_PORT}')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
