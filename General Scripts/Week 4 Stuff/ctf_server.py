#!/usr/bin/python3

# from https://docs.python.org/3/howto/sockets.html#non-blocking-sockets
# and
# https://docs.python.org/3/library/socket.html#example

# Test with 
# echo "hey" | nc crow 42424

import socket
import json

def sendWin(host, port):
    # nc -l -u 42422
    print("UDP target IP:", host)
    print("UDP target port:", port)
    message = "Win! The magic word is: Quagmire"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.sendto(bytes(message, "utf-8"), (host, port))
    sock.close()


# create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket to a public host, and a well-known port
hostname = socket.gethostname()
print("listening on interface " + hostname)
# This accepts a tuple...
serversocket.bind(('', 42424))
# become a server socket
serversocket.listen()


while True:
    conn, addr = serversocket.accept()
    with conn: # this is a socket! With syntax does not work on python 2
        try:
            conn.settimeout(5)
            conn.sendall(b'Say "please"')
            print('Connected by', addr)
            data = conn.recv(1024)
            print("heard:")
            print(data.decode('UTF-8'))
            strData = data.decode('UTF-8')

            # is it JSON?
            wasJson = False
            try:
                # {"host":"localhost", "port": 42422}
                # echo '{"host":"crow.cs.umanitoba.ca", "port": 42422}' | nc robin.cs.umanitoba.ca 42424
                jData = json.loads(strData)
                host = jData['host']
                port = jData['port']
                wasJson=True
            except:
                # it's fine....
                print("Not json" + strData)
                


            # just say something
            if wasJson:
                sendWin(host,port)
            elif strData.lower().find("please") >= 0:
                # echo please | nc localhost 42424
                conn.sendall(b'The word of the day is "https://www.youtube.com/watch?v=dQw4w9WgXcQ - it\'s somewhere else! Keep going! Send a json object that has keys "host" and "port" that you\'re listening on with UDP')
            else:
                conn.sendall(b'https://youtu.be/z0O32YA4Ibs?t=52')

        except Exception as e:
            print(e)