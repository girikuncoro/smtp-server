#!/usr/bin/python
import socket  # provide access to BSD socket interface
from threading import Thread, Lock
import random
import datetime
import time
import sys

# This is the multi-threaded client.  This program should be able to run
# with no arguments and should connect to "127.0.0.1" on port 8765.  It
# should run a total of 1000 operations, and be extremely likely to
# encounter all error conditions described in the README.

host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
toaddr = sys.argv[3] if len(sys.argv) > 3 else "nobody@example.com"
fromaddr = sys.argv[4] if len(sys.argv) > 4 else "nobody@example.com"

STATE = ["HELO", "MAIL FROM:", "RCPT TO:", "DATA", "", "INVALID CMD"]
ERROR = {
    "unrecognized": 500,
    "syntax": 501,
    "order": 503,
    "duplicate_helo": 503,
    "nested_mail": 503,
    "sender": 555,
    "recipient": 555,
    "timeout": 421
}
OK = {
    "correct": 250,
    "end_data": 354
}

N_CONNECTION = 1
N_COMMAND = 1000

class ConnectMulticlient(Thread):
    def __init__(self, n_test):
        Thread.__init__(self)
        self.n_test = n_test
        random.seed()  # pseudo random seed

    def send(self, socket, message):
        socket.send(message.encode('utf-8'))

    def get_message(self):
        args = random.randint(0, 3)
        m = random.randint(0,5)
        msg = STATE[m]
        white_space = random.randint(0, 1)
        email = random.randint(0, 1)
        status = None

        if msg != "DATA":
            if white_space:
                msg += " "

            if email:
                msg += toaddr

            for _ in range(args):
                msg += "arg "

            if STATE[m] == "":
                msg = "Email body\r\n."

        msg += "\r\n"

        if STATE[m] == "DATA":
            if args > 0 and not white_space:
                status = ERROR["syntax"]
            elif args > 0:
                status = ERROR["syntax"]
            else:
                status = OK["end_data"]

        if STATE[m] == "":
            status = OK["correct"]

        if STATE[m] == "INVALID CMD":
            status = ERROR["unrecognized"]

        # valid cmd other than DATA
        if STATE[m] not in ["DATA", "", "INVALID CMD"]:
            if white_space and args == 1:
                status = OK["correct"]
            elif white_space and not args:
                status = ERROR["syntax"]
            elif white_space and args > 1:
                if STATE[m] == "MAIL FROM:" or STATE[m] == "RCPT TO:":
                    status = ERROR["sender"]
                else:
                    status = ERROR["unrecognized"]

            if not white_space and not args:
                status = ERROR["syntax"]
            elif not white_space and args > 0:
                status = ERROR["unrecognized"]

        return (status, m, msg)

    def validate_response(self, cmd, resp, expected, r):
        status = int(r.split()[0])
        if cmd > 0 and STATE[resp] == "HELO":
            return ((status == ERROR["duplicate_helo"]), status)
        if cmd > 1 and STATE[resp] == "MAIL FROM:":
            return ((status == ERROR["nested_mail"]), status)
        if STATE[cmd] == "DATA":
            if resp == "RCPT TO:":
                return ((status == expected), status)  # additional RCPT
            if resp == "DATA":
                return ((status == expected), status)  # data body
            else:
                return ((status == ERROR["order"]), status)
        if STATE[cmd] == "HELO" and STATE[resp] != "HELO":
            return ((status == ERROR["duplicate_helo"]), status)
        if STATE[cmd] == resp:
            return ((status == expected), status)
        else:
            if expected == OK["correct"]:
                return ((status == ERROR["order"]), status)
            return ((status == expected), status)

    def run(self):
        cmd = 0  # current cmd point to state

        # initialize connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print s.recv(500)

        for _ in range(self.n_test):
            (status, resp, msg) = self.get_message()
            self.send(s, msg)
            print ">> {}".format(msg)

            r = s.recv(500)
            print "<< {}".format(r)

            (valid, error) = self.validate_response(cmd, resp, status, r)

            if valid:
                if (STATE[cmd] != "DATA" or resp != 2) and \
                    (error == OK["correct"] or error == OK["end_data"]):
                    cmd = (cmd+1)%5 if cmd < 4 else 1

                if (STATE[cmd] == "DATA" or resp != 2) and \
                    (error == OK["correct"] or error == OK["end_data"]):
                    cmd = (cmd+1)%5 if cmd < 4 else 1

for _ in range(N_CONNECTION):
    ConnectMulticlient(N_COMMAND / N_CONNECTION).start()
