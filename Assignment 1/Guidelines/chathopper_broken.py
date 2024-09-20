#!/usr/bin/python3

# started with https://docs.python.org/3/library/socket.html#example

# chat-hopper!
# Give the message to the next person

# _   _     _       _       _               _              
#| |_| |__ (_)___  (_)___  | |__  _ __ ___ | | _____ _ __  
#| __| '_ \| / __| | / __| | '_ \| '__/ _ \| |/ / _ \ '_ \ 
#| |_| | | | \__ \ | \__ \ | |_) | | | (_) |   <  __/ | | |
# \__|_| |_|_|___/ |_|___/ |_.__/|_|  \___/|_|\_\___|_| |_|
#                                                          
# this is currently broken!!!!!!
# Find the bug!

import socket
import sys
import select
import traceback

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port

lastWord = "F1rst p0st"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # blocking, but default
    # https://docs.python.org/3/library/socket.html#notes-on-socket-timeouts
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # overall timeout
    # Q: What happens if I remove this timeout, and the other one, too?
    s.settimeout(0)
    s.bind((HOST, PORT))
    s.listen()
    clients = []
    while True:
        try:
            inputs = [s] + clients 
            # only block
            readable, writable, exceptional = select.select(inputs, [], inputs)

            for client in readable:
                if client is s:
                    # new client
 

                    conn, addr = s.accept()
                    print('Connected by', addr)
                    clients.append(conn)
                if client in clients:     
                    data = client.recv(1024   )
                    print(data)
                    if data:
                        print('swapping')
                        currWord = lastWord
                        lastWord = data.strip()
                    conn.sendall(currWord)
                    conn.sendall(b'Bye!')
                    conn.close()

                    clients.remove(client)
        except KeyboardInterrupt as e:
            print("RIP")
            sys.exit(0)
        except Exception as e:
            print("Something happened... I guess...")
            print(e)
            print("Exception in user code:")
            print("-"*60)
            traceback.print_exc(file=sys.stdout)
            print("-"*60)


