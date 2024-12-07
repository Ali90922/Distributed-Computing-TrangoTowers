import socket
import threading

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 8000              # Arbitrary non-privileged port


page = '''<html>
<body>
Hey ya;; Youare teh {}th visitor, click here to claim your prize
</body>
</html>
'''

header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: {}

"""
counter = -1

def reply(conn, count):
    with conn:
        print('Connected by', addr)
        formattedPage = page.format(counter)
        replyHeader = header.format(len(formattedPage))
        conn.sendall(replyHeader.encode())
        conn.sendall(formattedPage.encode())


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        counter += 1
        myThread = threading.Thread(target=reply, args=(conn, counter))
        myThread.run()

