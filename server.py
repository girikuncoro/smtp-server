#!/usr/bin/python
import getopt
import socket
import sys
from threading import Thread

# Don't change 'host' and 'port' values below.  If you do, we will not be able to contact
# your server when grading.  Instead, you should provide command-line arguments to this
# program to select the IP and port on which you want to listen.  See below for more
# details.
host = "127.0.0.1"
port = 8765

# error messages to be sent in certain conditions
# ERROR = {
#     "syntax": {
#         "code": "501", "msg": "{} Syntax: proper syntax"},
#     "order": {
#         "code": "503", "msg": "{} Error: need {} command"},
#     "unrecognized": {
#         "code": "500", "msg": "{} Error: command not recognized"},
#     "duplicate": {
#         "code": "503", "msg": "{} Error: duplicate HELO"},
#     "nested": {
#         "code": "503", "msg": "{} Error: nested MAIL command"},
#     "sender": {
#         "code": "555", "msg": "{} <bad email>: Sender address rejected"},
#     "recipient": {
#         "code": "555", "msg": "{} <bad email>: Recipient address invalid"},
#     "timeout": {
#         "code": "421", "msg": "{} 4.4.2 gk256 Error: timeout exceeded"}
# }
ERROR = {
    "unrecognized": "500 Error: command not recognized",
    "syntax_helo": "501 Syntax: HELO yourhostname",
    "syntax_from": "501 Syntax: MAIL FROM: you@domain.com",
    "syntax_to": "501 Syntax: RCPT TO: sendto@domain.com",
    "order": "503 Error: need {} command",
    "duplicate": "503 Error: duplicate HELO",
    "nested": "503 Error: nested MAIL command",
    "sender": "555 {}: Sender address rejected",
    "recipient": "555 {}: Recipient address invalid",
    "timeout": "421 4.4.2 gk256 Error: timeout exceeded"
}

# ok message to be sent depending on state
OK = {
    "HELO": "250 gk256",
    "MAIL": "250 OK",
    "RCPT": "250 OK",
    "DATA": "354 End data with <CR><LF>.<CR><LF>",
    "END": "220 gk256 SMTP CS4410MP3"
}

# handle a single client request
class ConnectionHandler:
    def __init__(self, socket):
        self.socket = socket
        self.scounter = 0

    def handle(self):
        self.socket.close()
        pass

    def parse_msg(self):
        pass

    def parse_bulkmsg(self):
        pass

    def send_ok(self, next):
        pass

    def send_error(self, etype):
        REQUIRE_ARGS = ["order", "sender", "recipient"]

        if etype not in ERROR:
            msg = "Error type not recognized"

        if etype not in REQUIRE_ARGS:
            msg = ERROR[etype]
        elif etype == REQUIRE_ARGS[0]:
            msg = ERROR[etype].format(self.state[self.scounter+1])
        elif etype == REQUIRE_ARGS[1]:
            msg = ERROR[etype].format(self.from_mail)
        elif etype == REQUIRE_ARGS[2]:
            msg = ERROR[etype].format(self.to_mails.pop())

        # bad command will set the new timeout
        self.socket.settimeout(self.socket.gettimeout()/2)
        self.socket.send(msg)

    def format_txt(self):
        pass

    def is_validmail(self):
        pass

    # handle HELO command
    def parse_helo(self):
        pass

    # handle MAIL FROM command
    def parse_mail_from(self):
        pass

    # handle RCPT TO command
    def parse_rcpt_to(self):
        pass

    # handle DATA command
    def parse_data(self):
        pass


# thread pool
class ThreadPool:
    def __init__(self):
        pass

    def start_mailer():
        pass

    def finish_mailer():
        pass


# postman for each thread in the pool
class Mailer(Thread):
    def __init__(self):
        pass

    def run():
        pass


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
