# ----------------------------------------------------------------------------------------------
# Name: Kunal Rajpal
# Student number: 7885301
# Course: COMP 4300, Computer Network
# Instructor: Dr. Sara Rouhani 
# Assignment: Assignment 1, chat_client.py
# 
# Remarks: Client for our client-server application
#
#-------------------------------------------------------------------------------------------------

#Imports
import json
import socket
import threading
import sys

#Constants
# The host and port is chosen in accordance with the server
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080

welcome = "************************************\nWelcome! To the awesome chat room\nLet's get Started\n************************************\n"
print (welcome)


nickname = input("Please enter the nickname you wish to be identified with: \n")

#setting up TCP with our server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_HOST, SERVER_PORT))

introduction  = {
    "type":"welcome",
    "nick-name":nickname
}

# as soon as the server is joined our client sends out a nick name to the server as the welcome message
client.send(json.dumps(introduction).encode())

#------------------------------------------------------
# handle_messages
#
# PURPOSE: To receive and process messages from the server
#
#------------------------------------------------------
def handle_messages():

    while True:

        try:

            message = client.recv(1024)

            data_json = json.loads(message.decode('UTF-8'))

            if data_json["reply-type"] == "welcome-reply":
                print(data_json["output"])

            if data_json["reply-type"] == "existing-rooms-reply":

                listOfRooms = (list( (data_json["list_of_rooms"]).keys() ))

                # We print the room names in the list one by one
                print("All the active chat rooms are as follows:")

                for x in range(len(listOfRooms)):
                    print( "%d %s" %(x+1, listOfRooms[x]) )


            if data_json["reply-type"] == "room-info-reply":

                if (data_json["peers"]) == -1:
                    print(data_json["output"])
                elif (len(data_json["peers"])) == 0:
                    print(data_json["output"])
                else:
                    print(data_json["output"])
                    print("They are as follows:")
                    users = data_json["peers"]
                    for x in range(len(users)):
                        print("%d %s"% (x+1,users[x]))


            if data_json["reply-type"] == "join-room-reply":
                print(data_json["output"])
                #print(data_json["peers"])

            if data_json["reply-type"] == "create-room-reply":

                print(data_json["output"])


            if data_json["reply-type"] == "send-message-reply":

                print(data_json["list_of_rooms"])
            
            if data_json["reply-type"] == "leave-room-reply":

                print(data_json["output"])

        except Exception as e:

            continue




#------------------------------------------------------
#   We start a new thread to receive messages from the 
#   server and other clients
#
#------------------------------------------------------

handler = threading.Thread(target = handle_messages)
handler.start()

#------------------------------------------------------
#   This serves as our command menu and is displayed to the user 
#   when they first join
#
#------------------------------------------------------

cmd = """This is the list of commands you can utilize:\n
[*]ROOMS:       To get a list of all existing chat rooms
[*]ROOM-INFO:   Use this command followed by the name of the room to get the number and list of all connected users for the room
[*]JOIN-ROOM:   Use this command followed by the name of the room you wish to join to join the room
[*]CREATE-ROOM: Use this command followed by the name of the room you wish to create
[*]LEAVE-ROOM:  Use this command followed by the name of the room you wish to leave
[*]SEND:        Use this command followed by the name of the chatroom you wish to send your message in and your message\n"""

print(cmd)

#------------------------------------------------------
#   Our infinite loop runs to take input from the user
#   and send request to the server accordingly
#
#------------------------------------------------------

while True:
    command = input("Enter Command: \n")
    words = command.split(" ")
    n = len(words)
    if n <=0:
        print("Empty command entered")
    else:
        if words[0] == "ROOMS":

            request = {
                "type":"existing-rooms"
            }

            client.send(json.dumps(request).encode())

        elif words[0] == "ROOM-INFO":

            request = {
                "type":"room-info",
                "room-name":words[1]
            }

            client.send(json.dumps(request).encode())

        elif words[0] == "JOIN-ROOM":

            request = {
                "type":"join-room",
                "nick-name":nickname,
                "room-name":words[1]
            }

            client.send(json.dumps(request).encode())

        elif words[0] == "CREATE-ROOM":

            request = {
                "type":"create-room",
                "nick-name":nickname,
                "room-name":words[1]
            }

            client.send(json.dumps(request).encode())

        elif words[0] == "LEAVE-ROOM":

            request = {
                "type":"leave-room",
                "nick-name":nickname,
                "room-name":words[1]
            }

            client.send(json.dumps(request).encode())
        elif words[0] == "SEND":
            rm = words[1]
            strng = ""

            for x in range(len(words)):

                if x == 0 or x == 1:
                    continue
                else:
                    strng += words[x]
                
            request = {
                "type": "send-message",
                "room-name": rm,
                "letter":strng
            }

            client.send(json.dumps(request).encode())
        elif words[0] == "EXIT":
            sys.exit("Exit successful")
            print("Exit")

        else:
            print("Invalid command entered, please try again!")
