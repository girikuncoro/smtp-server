#!/usr/bin/python

import getopt
import socket
import sys

# Don't change 'host' and 'port' values below.  If you do, we will not be able to contact 
# your server when grading.  Instead, you should provide command-line arguments to this
# program to select the IP and port on which you want to listen.  See below for more
# details.
host = "127.0.0.1"
port = 8765

# handle a single client request
class ConnectionHandler:
    def __init__(self, socket):
        self.socket = socket

    def handle(self):
        self.socket.close()

# the main server loop
def serverloop():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # mark the socket so we can rebind quickly to this port number
    # after the socket is closed
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind the socket to the local loopback IP address and special port
    serversocket.bind((host, port))
    # start listening with a backlog of 5 connections
    serversocket.listen(5)

    while True:
        # accept a connection
        (clientsocket, address) = serversocket.accept()
        ct = ConnectionHandler(clientsocket)
        ct.handle()

# You don't have to change below this line.  You can pass command-line arguments
# -h/--host [IP] -p/--port [PORT] to put your server on a different IP/port.
opts, args = getopt.getopt(sys.argv[1:], 'h:p:', ['host=', 'port='])

for k, v in opts:
    if k in ('-h', '--host'):
        host = v
    if k in ('-p', '--port'):
        port = int(v)

print("Server coming up on %s:%i" % (host, port))
serverloop()
