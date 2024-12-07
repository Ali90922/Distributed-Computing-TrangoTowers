import cmd
import sys
import re
import json
import socket
import pprint

pp = pprint.PrettyPrinter(indent=4)

statsMessage = {
    "type": "STATS"
}


class TestShell(cmd.Cmd):
    intro = 'Welcome to the 3010 verifier shell version 2.   Type help or ? to list commands.\n'
    prompt = '3010 > '
    coordinatorSock = None

    def preloop(self) -> None:
        '''
        Initialize UDP socket
        '''
        if len(sys.argv) < 2:
            print("Open with two arguments: peerHostName peerPort")
            sys.exit(1)
        try:
            self.hostname = sys.argv[1]
            try:
                self.port = int(sys.argv[2])
            except:
                print("Bad port number")
                sys.exit(1)

            print("Creating UDP socket")
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)
            # bind to 0 will give us a "random" port
            self.sock.bind(('', 0))
            self.sock.settimeout(5)

            # We could print what socket we have
            # 0.0.0.0 is the "all interfaces" phony ip address
            # print(self.sock.getsockname())

            print("Test send to peer {}:{}".format(self.hostname, self.port))
            try:
                msg = json.dumps(statsMessage)
                self.sock.sendto(msg.encode(), (self.hostname, self.port))
                # listen for it...
                response = self.sock.recv(1024)
                stats = json.loads(response)
                print("Connected! Chain is height {} with hash {}".format(
                    stats['height'],
                    stats['hash']
                ))
            except socket.timeout:
                print("Timed out! Peer not responding?")
                sys.exit(1)
            except json.JSONDecodeError:
                print("Got a reply, but it was not json")
                print(response)
            except Exception as e:
                print("Whoa... not sure.")
                print(e)
                sys.exit(1)

        except Exception as e:
            print("Could not connect. Quitting")
            print(e)
            sys.exit(1)

    def do_add(self, arg):
        '''
        add a word for mining. Must have a word
        '''

        if len(arg) == 0:
            print("Require an argument")
            return

        try:
            content = {
                "type": "NEW_WORD",
                "word": arg
            }

            self.sock.sendto(json.dumps(content).encode(),
                             (self.hostname, self.port))
            # has no reply
        except Exception as e:
            print("Error sending")
            print(e)

    def do_stats(self, arg):
        '''
        Gets status from this peer
        '''
        try:
            msg = json.dumps(statsMessage)
            self.sock.sendto(msg.encode(), (self.hostname, self.port))
            # listen for it...
            response = self.sock.recv(1024)
            stats = json.loads(response)
            print("Connected! Chain is height {} with hash {}".format(
                stats['height'],
                stats['hash']
            ))
        except socket.timeout:
            print("Timed out! Peer not responding?")
            sys.exit(1)
        except json.JSONDecodeError:
            print("Got a reply, but it was not json")
            print(response)
        except Exception as e:
            print("Whoa... not sure.")
            print(e)
            sys.exit(1)

    def do_consensus(self, arg):
        '''
        Tell the peer to do a consensus
        '''

        try:
            content = {
                "type": "CONSENSUS",
            }

            self.sock.sendto(json.dumps(content).encode(),
                             (self.hostname, self.port))
            # has no reply
        except Exception as e:
            print("Error sending")
            print(e)

    def do_get(self, arg):
        '''
        get a single link from the chain. Usage get id
        '''

        if len(arg) == 0:
            print("Gimme dat number")
        else:

            try:
                content = {
                    "type": "GET_BLOCK",
                    "height": int(arg)
                }

                self.sock.sendto(json.dumps(content).encode(),
                                 (self.hostname, self.port))
                # wait for reply
                try:
                    response = self.sock.recv(1024)
                    pp.pprint(json.loads(response))
                except json.JSONDecodeError:
                    print("Got bad json in return")
                    print(response)
                except socket.timeout:
                    print("Timed out")
            except ValueError:
                print("id must be numeric")
            except Exception as e:
                print("Error sending/receiving")
                print(type(e))
                print(e)

    def do_exit(self, arg):
        print('Later, gator.')
        return True

    def do_EOF(self, arg):
        print('The cool way to exit!')
        return True

    def postloop(self) -> None:
        try:
            if self.sock is not None:
                self.sock.close()
        except:
            print("Failed to close the socket!")


if __name__ == '__main__':
    TestShell().cmdloop()
