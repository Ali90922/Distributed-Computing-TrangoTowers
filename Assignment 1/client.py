import socket
import threading 


Nickname = input("Choose a Nickname")

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
client.connect(('127.0.0.1',55456))


def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if(message == 'NICK'):
                client.send(Nickname.encode('ascii'))
            else:
                print(message)

        except:
            print("An error occured !")
            client.close()
            break