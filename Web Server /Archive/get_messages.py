import socket

CHAT_SERVER_HOST = 'localhost'
CHAT_SERVER_PORT = 8547

def get_messages():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
            s.sendall(b'GET_MESSAGES')
            messages = ""
            while True:
                chunk = s.recv(1024)
                if not chunk:
                    break
                messages += chunk.decode()
            print("Received messages:\n", messages)
    except Exception as e:
        print("Error retrieving messages:", e)

get_messages()

