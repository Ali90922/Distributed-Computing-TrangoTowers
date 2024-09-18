# Echo server program
import socket

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 5000               # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    # Block!
    while True:
        conn, addr = s.accept()
        conn.settimeout(1)
        try:
            with conn:
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    if not data: break
                    conn.sendall(data)
                    print(data.decode('utf-8'))
        except TimeoutError as te:
            print("timed out!")
             

