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

