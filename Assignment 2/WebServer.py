import socket
import json
from http import cookies
import threading
import os
import mimetypes
from urllib.parse import urlparse, parse_qs

CHAT_SERVER_HOST = 'localhost'
CHAT_SERVER_PORT = 8547
WEB_SERVER_PORT = 8548

# Basic response headers
def send_response_header(client, status_code, content_type="text/html", headers=None):
    client.send(f"HTTP/1.1 {status_code}\r\n".encode())
    client.send(f"Content-Type: {content_type}\r\n".encode())
    if headers:
        for header, value in headers.items():
            client.send(f"{header}: {value}\r\n".encode())
    client.send("\r\n".encode())

# Check if the user is logged in by looking for 'nickname' in cookies
def is_logged_in(headers):
    if "Cookie" in headers:
        c = cookies.SimpleCookie(headers["Cookie"])
        return "nickname" in c
    return False

# Handle GET requests
def handle_get_request(client, path, headers):
    url_parts = urlparse(path)
    path = url_parts.path
    query_params = parse_qs(url_parts.query)
    limit = int(query_params.get("limit", [None])[0]) if "limit" in query_params else None
    
    if path == '/api/messages':
        if not is_logged_in(headers):
            send_response_header(client, "403 Forbidden", "application/json")
            client.send(b'{"error": "Not logged in"}')
            return
        handle_get_messages(client, limit)
    elif path == '/':
        # Serve index.html if root path
        path = '/index.html'
        serve_static_file(client, path.lstrip('/'))
    else:
        serve_static_file(client, path.lstrip('/'))

# Serve static files
def serve_static_file(client, file_path):
    if os.path.isfile(file_path):
        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"
        try:
            with open(file_path, 'rb') as file:
                send_response_header(client, "200 OK", content_type)
                client.send(file.read())
        except Exception as e:
            print(f"Error serving file {file_path}: {e}")
            send_response_header(client, "500 Internal Server Error")
            client.send(b"<h1>500 Internal Server Error</h1>")
    else:
        send_response_header(client, "404 Not Found")
        client.send(b"<h1>404 Not Found</h1>")

# Handle POST requests
def handle_post_request(client, path, headers, body):
    if path == '/api/messages':
        if not is_logged_in(headers):
            send_response_header(client, "403 Forbidden", "application/json")
            client.send(b'{"error": "Not logged in"}')
            return
        handle_post_message(client, headers, body)
    elif path == '/api/login':
        handle_login(client, body)
    else:
        send_response_header(client, "404 Not Found")
        client.send(b"<h1>API Endpoint Not Found</h1>")

# Handle DELETE requests
def handle_delete_request(client, path):
    if path == '/api/login':
        handle_logout(client)
    else:
        send_response_header(client, "404 Not Found")
        client.send(b"<h1>API Endpoint Not Found</h1>")



# problem popping up in the post message function as it is displaying the nick-name sent from the commandline client twice 
    # have to fix the above problem !!!! ^
        # Problem is fixed - problem was with the old Clien.py file logging in the nickname twice - nothing wrong with this file

# Retrieve messages from chat server with optional limit
def handle_get_messages(client, limit=None):
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

        # Split messages and apply limit if specified
        message_list = messages.splitlines()
        if limit:
            message_list = message_list[:limit]

        # Ensure we don't prepend nickname again if it's already included
        processed_messages = []
        for message in message_list:
            if message.count(":") > 1:  # Detect if there is already a nickname in the format
                # Split the message once to get nickname and content
                nickname, content = message.split(":", 1)
                processed_messages.append(f"{nickname.strip()}: {content.strip()}")
            else:
                processed_messages.append(message.strip())

        send_response_header(client, "200 OK", "application/json")
        client.send(json.dumps({"messages": processed_messages}).encode())
    except Exception as e:
        print(f"Error in handle_get_messages: {e}")
        send_response_header(client, "500 Internal Server Error")
        client.send(f"Failed to retrieve messages: {e}".encode())







# Send a new message to the chat server
def handle_post_message(client, headers, body):
    if not body.strip():
        send_response_header(client, "400 Bad Request")
        client.send(b"Empty request body")
        return
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        send_response_header(client, "400 Bad Request")
        client.send(b"Malformed JSON data")
        return

    message = data.get('message', '')
    if not message:
        send_response_header(client, "400 Bad Request")
        client.send(b"No message content")
        return

    nickname = "Anonymous"
    if "Cookie" in headers:
        c = cookies.SimpleCookie(headers["Cookie"])
        nickname = c.get("nickname").value if "nickname" in c else nickname

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
            full_message = f'SEND_MESSAGE {nickname}: {message}'
            s.sendall(full_message.encode('ascii'))
            print(f"Message sent to chat server: {full_message}")

        send_response_header(client, "201 Created")
        client.send(b"Message sent")
    except Exception as e:
        print(f"Error in handle_post_message: {e}")
        send_response_header(client, "500 Internal Server Error")
        client.send(f"Failed to send message: {e}".encode())








        

# Set login cookie
def handle_login(client, body):
    if not body.strip():
        send_response_header(client, "400 Bad Request")
        client.send(b"Empty request body")
        return
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        send_response_header(client, "400 Bad Request")
        client.send(b"Malformed JSON data")
        return

    nickname = data.get('nickname', 'Anonymous')
    c = cookies.SimpleCookie()
    c['nickname'] = nickname
    c['nickname']['httponly'] = True
    c['nickname']['max-age'] = 3600 * 24 * 30  # Cookie lasts for 30 days

    send_response_header(client, "200 OK", headers={"Set-Cookie": c.output(header='', sep='')})
    client.send(b"Logged in")






# Logout and clear the nickname cookie
def handle_logout(client):
    send_response_header(client, "200 OK", headers={"Set-Cookie": "nickname=; Max-Age=0"})
    client.send(b"Logged out")





# Handle incoming client requests
def handle_client(client):
    try:
        request = client.recv(4096).decode()
        headers, body = request.split('\r\n\r\n', 1)
        request_line, *header_lines = headers.splitlines()
        
        method, path, _ = request_line.split()
        header_dict = {}
        
        for line in header_lines:
            key, value = line.split(":", 1)
            header_dict[key.strip()] = value.strip()

        if method == 'GET':
            handle_get_request(client, path, header_dict)
        elif method == 'POST':
            handle_post_request(client, path, header_dict, body)
        elif method == 'DELETE':
            handle_delete_request(client, path)
        else:
            send_response_header(client, "405 Method Not Allowed")
            client.send(b"Method Not Allowed")
    except Exception as e:
        print(f"Error handling client request: {e}")
    finally:
        client.close()





# Start the web server
def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('', WEB_SERVER_PORT))
        server.listen(5)
        print(f'Starting server on port {WEB_SERVER_PORT}...')
        
        while True:
            try:
                client, addr = server.accept()
                print(f"Connection from {addr}")
                threading.Thread(target=handle_client, args=(client,)).start()
            except KeyboardInterrupt:
                print("Shutting down server.")
                break

if __name__ == '__main__':
    run_server()
