# ----------------------------------------------------------------------------------------------
# Name: Kunal Rajpal
# Student number: 7885301
# Course: COMP 4300, Computer Network
# Instructor: Dr. Sara Rouhani 
# Assignment: Assignment 1, chat_server.py
# 
# Remarks: Server for our client-server application
#
#-------------------------------------------------------------------------------------------------

#Imports
import json
import socket
import threading 


#Constants
SERVER_HOST = "127.0.0.1" #Local host
SERVER_PORT = 8080        #Any arbitrary port chosen

MAXIMUM_CAPACITY = 5      #Max capacity of the chat rooms

#------------------------------------------------------
# server set up
#   
# creating a TCP server connection 
# binding it to local host with a tuple containing our host and port
#------------------------------------------------------
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # The first parameter indicates we are using internet socket and the second parameter indicates we are using TCP and not UDP
server.bind((SERVER_HOST, SERVER_PORT))
server.listen()                                             # listening mode

print("Listening on %s:%d" % (SERVER_HOST, SERVER_PORT))    

#Lists & Dictionaries
list_of_clients = []        #list of clients connecting to the server
client_nicknames = []       #list of client nicknames
chat_rooms = {}             #Dictionary of all existing chart rooms
# our dict will have the name of the chat room as the key with its value being the list of peers in that chat room


#Functions


#------------------------------------------------------
# broadcast
#
# PURPOSE: A helper function to send messages to a particular list of clients
#
# INPUT PARAMETERS: Message to be sent
#                   Clients that the message will be broadcasted to
#                   broadcasting client
#------------------------------------------------------
def broadcast(message, targetClients, broadcaster):
    for targetClient in targetClients:
        if targetClient != broadcaster:
            try:
                targetClient.send(message)
            except Exception as e:
                continue


#------------------------------------------------------
# remove
#
# PURPOSE: Helper function to remove a client from our client list
#
# INPUT PARAMETERS: client to be removed
#------------------------------------------------------
def remove(thisClient):
    if thisClient in list_of_clients:
        list_of_clients.remove(thisClient)


#------------------------------------------------------
# welcome
#
# PURPOSE: Helper function to send a reply to a new client who just sent the server their nick name
#
# INPUT PARAMETERS: the nick name of the client
#                   the client
#------------------------------------------------------
def welcome(newNickName, conn):

    if newNickName in client_nicknames:
        msg = "Error: Sorry the nickname already exists!"

    else:
        msg = "\n*****************************************\n\nHello %s! Welcome to the awesome chat room, we hope you brought pizza\n\n*****************************************"%newNickName
        print("A new user joined the chat! Welcome: " + newNickName)
        client_nicknames.append(newNickName)

    reply = {
        "reply-type":"welcome-reply",
        "output": msg 
    }

    conn.send(json.dumps(reply).encode())

#------------------------------------------------------
# existing_rooms
#
# PURPOSE: To return the list of all existing chat rooms 
#
# INPUT PARAMETERS: the client requesting the list
#------------------------------------------------------
def existing_rooms(conn):
    
    reply = {
        "reply-type":"existing-rooms-reply",
        "list_of_rooms": chat_rooms # you will need to parse this in the client side to get a list of all the names of the chat rooms #TODO
    }

    conn.send(json.dumps(reply).encode())


#------------------------------------------------------
# room_info
#
# PURPOSE: To return the list & number of all users in a particular chat room
#
# INPUT PARAMETERS: the client requesting the list, the chat room 
#------------------------------------------------------
def room_info(conn, room):

    if room in chat_rooms:

        theList = chat_rooms[room]  #list of all the users
        length = len(theList)       #the number of users in the room
        msg = "The chat room %s has %d users. "%(room, length)

    else:
        theList = -1
        msg = "The room name entered does not match any active existing rooms. Please try again"

    reply = {
        "reply-type":"room-info-reply",
        "peers": theList,
        "output": msg
    }

    conn.send(json.dumps(reply).encode())

#------------------------------------------------------
# join_room
#
# PURPOSE: To add a client to any particular chat room
#
# INPUT PARAMETERS: the client to be added
#                   chat room to be joined
#                   nick name of the client 
#------------------------------------------------------
def join_room(conn, roomToJoin, nick):

    if roomToJoin in chat_rooms:
        #we attempt to join
        theUserList = chat_rooms[roomToJoin]
        length = len(theUserList)

        if length >= 5:
            msg = "Failed joining the room. The room has reached its maximum capacity"
        elif length < 5:
            #we can join
            theUserList.append(nick)
            msg= "Successfully joined the room %s"%roomToJoin
        else: 
            msg = "error"
            print("error in join_room")
    
    else:
        # we can not join. Does not exist
        msg = "The room name entered does not match any active existing rooms. Please try again"

    reply = {
        "reply-type":"join-room-reply",
        "list_of_rooms": chat_rooms,
        "peers": theUserList,
        "output": msg
    }

    conn.send(json.dumps(reply).encode())


#------------------------------------------------------
# create_room
#
# PURPOSE: To create a new chat room
#
# INPUT PARAMETERS: the client that requested the new room
#                   name of the chat room
#                   nick name of the client 
#------------------------------------------------------
def create_room(conn, room_name, nick):

    if room_name in chat_rooms:
        
        msg = "Please pick a different room name, another room with the same name already exists"

    else:
        #add the name as the key and the list of nicknames as value in the dictionary
        chat_rooms[room_name] = []
        msg = "The room %s has been created. You can now look at the updated list of chat rooms using the appropriate command"%room_name
        print("A new room %s has been created by the user %s"%room_name%nick)

    reply = {
        "reply-type":"create-room-reply",
        "list_of_rooms": chat_rooms,
        "output": msg
    }
    conn.send(json.dumps(reply).encode())

    

#------------------------------------------------------
# send_message
#
# PURPOSE: To send message to a particular chat room
#
# INPUT PARAMETERS: the client that wants to send the message
#                   name of the chat room
#                   nick name of the client 
#------------------------------------------------------
def send_message(conn, rm, msgString):
    if rm in chat_rooms:
        msg = "sending message bro"
        userList = chat_rooms[rm]
        broadcast( msgString, userList, conn)
    else:
        msg = "The room name could not be found"

    reply={
        "reply-type":"send-message-reply"
    }

    conn.send(json.dumps(reply).encode())
    print("reply sent")

#------------------------------------------------------
# leave_room
#
# PURPOSE: To exit any chat room
#
# INPUT PARAMETERS: the client that wishes to leave the chat room
#                   name of the chat room
#                   nick name of the client 
#------------------------------------------------------
def leave_room(conn, roomToBeLeft, nick):
    
    if roomToBeLeft in chat_rooms:

        if nick in chat_rooms[roomToBeLeft]:
            
            (chat_rooms[roomToBeLeft]).remove(nick)
            msg = "Leaving room successful"      
    else:
        msg = "The room does not exist"

    reply={
        "reply-type":"leave-room-reply",
        "list_of_rooms": chat_rooms,
        "output": msg
    }

    conn.send(json.dumps(reply).encode())

#------------------------------------------------------
# client_handler
#
# PURPOSE: Handles all the requests made by any client
#
# INPUT PARAMETERS: the client and their address
#
# This function only calls the helper functions to complete the tasks
#------------------------------------------------------
def client_handler(client, address):

    while True:
        try:
            message = client.recv(1024)

            data_json = json.loads(message.decode('UTF-8'))

            if data_json["type"] == "welcome":
                welcome(data_json["nick-name"], client)

            if data_json["type"] == "existing-rooms":
                #View list of existing chat rooms
                existing_rooms(client)

            if data_json["type"] == "room-info":
                #view the number and list of connected users for each room
                room_info(client, data_json["room-name"])

            if data_json["type"] == "join-room":
                #Join existing chat rooms if the room capacity is not full
                join_room(client, data_json["room-name"], data_json["nick-name"])

            if data_json["type"] == "create-room":
                #Create chat-rooms
                create_room(client, data_json["room-name"], data_json["nick-name"])

            if data_json["type"] == "send-message":
                #Send messages to chat-rooms
                send_message(data_json["letter", data_json["room-name"],client ])
            
            if data_json["type"] == "leave-room":
                #Leave a chat-room
                leave_room(client, data_json["room-name"], data_json["nick-name"])

        except Exception as e:
            continue

#
#------------------------------------------------------
#
# infinite loop to listen for clients
#
# We start separate threads fro every client to keep the connection opn
#------------------------------------------------------
while True:
    client, address = server.accept()
    
    list_of_clients.append(address)

    handler = threading.Thread(target = client_handler, args=(client,address)) #The threads are targeted to the message handler for the clients
    handler.start()

