Last login: Tue Sep 24 18:50:18 on ttys013

The default interactive shell is now zsh.
To update your account to use zsh, please run `chsh -s /bin/zsh`.
For more details, please visit https://support.apple.com/kb/HT208050.
(base) wifi-wpa-cw2-140-193-121-143:~ Ali_Nawaz$ ssh nawaza1@aviary.cs.umanitoba.ca
(nawaza1@aviary.cs.umanitoba.ca) Password: 
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.8.0-45-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

Logged into host hawk.cs.umanitoba.ca

2 devices have a firmware upgrade available.
Run `fwupdmgr get-upgrades` for more information.

You have no mail.
Last login: Tue Sep 24 11:36:05 2024 from 140.193.125.44
Tue Sep 24 18:52:46 CDT 2024
 
tanjc    pts/0        Sep 24 17:09 (130.179.218.8)
nawaza1  pts/1        Sep 24 18:52 (140.193.121.143)
 
[nawaza1@hawk ~]> ls
 2160	  'Assignment 2'   Documents   Mail    Pictures   Templates   comp2160-a2   comp2160-a44    mail	 scp
 3010	   DHA		   Downloads   Music   Public	  Videos      comp2160-a3   comp2160-a444   my_program	 snap
 A4_2160   Desktop	   GILGIT      Path    Sialkot	  bin	      comp2160-a4   comp2160-al     quiz1	 src
[nawaza1@hawk ~]> cd GILGIT
[nawaza1@hawk ~/GILGIT]> ls
'Assignment 1 2150.iml'  'Light 2150.iml'   VPN   a1_data_sampleOutput.txt   out
[nawaza1@hawk ~/GILGIT]> cd
[nawaza1@hawk ~]> cd 3010
[nawaza1@hawk ~/3010]> ls
BrokenChatHopper  C33  Cl22  Client11.py  chat-hopper-fixed.py	client.py
[nawaza1@hawk ~/3010]> nano C33

  GNU nano 6.2                                                                  C33                                                                           
import socket
import json

HOST, PORT = "localhost", 42424

m = '{"id": 2, "name": "please"}'
jsonObj = json.loads(m)

# Convert the dictionary to a JSON string and then encode it to bytes
data = json.dumps(jsonObj).encode('utf-8')

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(data)

    # Receive data from the server and shut down
    received = sock.recv(1024)
finally:
    sock.close()

print("Sent:     {}".format(data))
print("Received: {}".format(received.decode('utf-8')))
# go over telnet again, mate 






                                  
