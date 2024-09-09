import socket
import sys
import select

serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# non-blocking, so that select can deal with the multiplexing
serversocket.setblocking(False)

# bind the socket to a public host, and a well-known port
hostname = socket.gethostname()
print("listening on interface " + hostname)
# This accepts a tuple...
serversocket.bind((socket.gethostname(), 42424))

# also listen on local
localsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# non-blocking, so that select can deal with the multiplexing
localsocket.setblocking(False)
# This accepts a tuple...
localsocket.bind(('127.0.0.1', 42000))

inputs = [serversocket, localsocket]
outputs = [] # None

while True: #FOREVAR 
  try:
    
    print("waiting for input")
    readable, writable, exceptional = select.select(inputs, outputs, inputs)
    # Read what we can, from where we can
    for source in readable:
      data, addr = source.recvfrom(1024)
      if source is localsocket:
        print("heard locally:")
      elif source is serversocket:
        print("heard externally:")
      print(data.decode('UTF-8'))
      # just say something
      print("Connection from:")
      print(addr)


  except KeyboardInterrupt:
    print("I guess I'll just die")
    serversocket.close()
    localsocket.close()
    sys.exit(0)
  except Exception as e:
    print("SOMETHING IS BAD")
    print(e)
