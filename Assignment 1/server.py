# ----------------------------------------------------------------------------------------------
# Name: Ali Nawaz
# Student number: 7951458
# Course: COMP 3010, Distributed Computing
# Instructor: Saulo 
# Assignment: Assignment 1, chat_server.py
# 
# Remarks: Server for our client-server application
#
#-------------------------------------------------------------------------------------------------


import socket
import threading



host = '127.0.0.1'    # Local host Ip address
port = 55456



# The first parameter means we are using internet socket and  second indicates we are using TCP and not UDP.
server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 


server.bind((host,port))     # Binding the server to our host
server.listen()           # Server starts listening to incoming methods

clients = []
Nicknames = []



# Broadcast function
def Broadcast(message):
    for client in clients:
        client.send(message)



# Handle the client 
        def handle(client):
            while(True):
                try:
                    message = client.recv(1024)
                    Broadcast(message)
                except:
                    index = clients.index(client)
                    clients.remove(client)
                    client.close()
                    Nickname = Nicknames[index]
                    Broadcast(f'{Nickname} has left the chat !!'.encode('ascii'))
                    Nicknames.remove(Nickname)
                    break



def recieve():
    while True:
        client,address = server.accept()
        print(f"Connected with {str(address)}")
        client.send("NICK".encode('ascii'))
        Nickname = client.recv(1024).decode('ascii')
        Nicknames.append(Nickname)
        clients.append(client)

        print(f'Nickname of the client is {Nickname} !')
        Broadcast(f'{Nickname} joined the chat lads !'.encode(ascii))
        client.send('You are connected to the server bud!'.encode(ascii))


        thread = threading.Thread(target=handle,args=(client,))
        thread.start()
print("Server is listening ......")
recieve()          






