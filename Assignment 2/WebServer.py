import socket
import threading
import json
import re
from http import cookies

CHAT_SERVER_HOST = 'localhost'
CHAT_SERVER_PORT = 8547
WEB_SERVER_PORT = 8000

# Basic response headers
def send_response_header(client, status_code, content_type="text/html", headers=None):
    client.send(f"HTTP/1.1 {status_code}\r\n".encode())
    client.send(f"Content-Type: {content_type}\r\n".encode())
    if headers:
        for header, value in headers.items():
            client.send(f"{header}: {value}\r\n".encode())
    client.send("\r\n".encode())

# Handle GET requests
def handle_get_request(client, path):
    if path == '/':
        # Serve index.html file
        try:
            with open('index.html', 'rb') as file:
                send_response_header(client, "200 OK", "text/html")
                client.send(file.read())
        except FileNotFoundError:
            send_response_header(client, "404 Not Found")
            client.send(b"<h1>404 Not Found</h1>")
    elif path.startswith('/api/messages'):
        handle_get_messages(client)
    else:
        send_response_header(client, "404 Not Found")
        client.send(b"<h1>404 Not Found</h1>")


# Handle POST requests
def handle_post_request(client, path, headers, body):
    if path == '/api/messages':
        handle_post_message(client, headers, body)
    elif path == '/api/login':
        handle_login(client, body)
    elif path == '/api/logout':
        handle_logout(client)
    else:
        send_response_header(client, "404 Not Found")
        client.send(b"<h1>404 Not Found</h1>")

def handle_get_messages(client):
    """Retrieve messages from chat server."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
            s.sendall(b'GET_MESSAGES')
            
            messages = ""
            while True:
                chunk = s.recv(1024)
                if not chunk:
                    break
                messages += chunk.decode('ascii')

        send_response_header(client, "200 OK", "application/json")
        client.send(json.dumps({"messages": messages.splitlines()}).encode())
    except Exception as e:
        print(f"Error in handle_get_messages: {e}")
        send_response_header(client, "500 Internal Server Error")
        client.send(f"Failed to retrieve messages: {e}".encode())

def handle_post_message(client, headers, body):
    """Send a new message to the chat server."""
    if not body.strip():
        # Handle empty body case
        send_response_header(client, "400 Bad Request")
        client.send(b"Empty request body")
        return
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        # Handle malformed JSON
        send_response_header(client, "400 Bad Request")
        client.send(b"Malformed JSON data")
        return

    message = data.get('message', '')
    
    # Retrieve nickname from cookie if available
    nickname = "Anonymous"
    if "Cookie" in headers:
        c = cookies.SimpleCookie(headers["Cookie"])
        nickname = c.get("nickname").value if "nickname" in c else nickname

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Reduced timeout for quicker response
            s.connect((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
            full_message = f'SEND_MESSAGE {nickname}: {message}'
            s.sendall(full_message.encode('ascii'))
            print(f"Message sent successfully: {full_message}")

        send_response_header(client, "201 Created")
        client.send(b"Message sent")
    except Exception as e:
        print(f"Error in handle_post_message: {e}")
        send_response_header(client, "500 Internal Server Error")
        client.send(f"Failed to send message: {e}".encode())


def handle_login(client, body):
    """Log in user and set a cookie."""
    if not body.strip():
        # Handle empty body case
        send_response_header(client, "400 Bad Request")
        client.send(b"Empty request body")
        return
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        # Handle malformed JSON
        send_response_header(client, "400 Bad Request")
        client.send(b"Malformed JSON data")
        return

    nickname = data.get('nickname', 'Anonymous')

    # Set the nickname as a cookie
    c = cookies.SimpleCookie()
    c['nickname'] = nickname
    c['nickname']['httponly'] = True

    send_response_header(client, "200 OK", headers={"Set-Cookie": c.output(header='', sep='')})
    client.send(b"Logged in")



def handle_logout(client):
    """Logs out a user by clearing the nickname cookie."""
    send_response_header(client, "200 OK", headers={"Set-Cookie": "nickname=; Max-Age=0"})
    client.send(b"Logged out")

def handle_client(client):
    """Handles each client connection."""
    request = client.recv(1024).decode()
    headers, body = request.split('\r\n\r\n', 1)
    request_line, *header_lines = headers.splitlines()
    
    # Parse request line
    method, path, _ = request_line.split()
    header_dict = {}
    
    # Parse headers
    for line in header_lines:
        key, value = line.split(":", 1)
        header_dict[key.strip()] = value.strip()

    # Route based on HTTP method
    if method == 'GET':
        handle_get_request(client, path)
    elif method == 'POST':
        handle_post_request(client, path, header_dict, body)
    else:
        send_response_header(client, "405 Method Not Allowed")
        client.send(b"Method Not Allowed")

    client.close()

def run_server():
    """Runs the multi-threaded server using socket and threading."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(('', WEB_SERVER_PORT))
        server.listen(5)
        print(f'Starting server on port {WEB_SERVER_PORT}...')
        
        while True:
            client, addr = server.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == '__main__':
    run_server()
