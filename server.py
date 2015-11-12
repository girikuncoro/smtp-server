#!/usr/bin/python
import getopt
import socket
import sys
import re
from shutil import copy  # to copy files in backup
from threading import Thread, Lock, Condition

# Don't change 'host' and 'port' values below.  If you do, we will not be able to contact
# your server when grading.  Instead, you should provide command-line arguments to this
# program to select the IP and port on which you want to listen.  See below for more
# details.
host = "127.0.0.1"
port = 8765

# error messages to be sent in certain conditions
ERROR = {
    "unrecognized": "500 Error: command not recognized",
    "syntax_helo": "501 Syntax: HELO yourhostname",
    "syntax_from": "501 Syntax: MAIL FROM: you@domain.com",
    "syntax_to": "501 Syntax: RCPT TO: sendto@domain.com",
    "syntax_data": "501 Syntax: DATA <CR><LF> message <CR><LF>.<CR><LF>",
    "order": "503 Error: need {} command",
    "duplicate_helo": "503 Error: duplicate HELO",
    "nested_mail": "503 Error: nested MAIL command",
    "sender": "555 {}: Sender address rejected",
    "recipient": "555 {}: Recipient address invalid",
    "timeout": "421 4.4.2 gk256 Error: timeout exceeded"
}

# ok message to be sent depending on state
OK = {
    "INIT": "220 gk256 SMTP CS4410MP3",
    "HELO": "250 gk256",
    "MAIL": "250 OK",
    "RCPT": "250 OK",
    "DATA": "354 End data with <CR><LF>.<CR><LF>",
    "FIN": "250 OK: Delivered {} messages"
}

FINISH = "FIN"

# handle a single client request
class ConnectionHandler(Thread):
    def __init__(self, thread_pool):
        Thread.__init__(self)
        self.pool = thread_pool
        self.mailbox_lock = Lock()

        self.TIMEOUT = 30

        self.s_pointer = 0  # state pointer
        self.states = ["INIT", "HELO", "MAIL", "RCPT", "DATA", "FIN"]

        self.client_name = ""
        self.from_mail = ""
        self.to_mails = []

        self.count_msg = 0
        self.text_body = ""

    # main handler
    def handle(self):
        self.send_ok("INIT")
        # print "Connect to {}".format(self.address)
        while self.states[self.s_pointer] != FINISH:
            self.parse_buffer(self.socket.recv(500))
        self.socket.close()

    def parse_buffer(self, messages):
        args = messages.split("\r\n")
        head_msg = args[0]
        tail_msg = args[1:-1]

        self.parse(head_msg)

        # ****TODO*****
        # self.parse_msg something

        for m in tail_msg:
            self.parse(m)

    def parse(self, msg):
        args = msg.split()
        cmd = args[0].upper() if len(args) > 0 else ""
        tail = args[1].upper() if len(args) > 1 else ""

        input_cmd = " ".join([cmd, tail]).strip() if cmd in ["MAIL", "RCPT"] \
                                                  else cmd

        cmd_list = ["HELO", "MAIL FROM:", "RCPT TO:", "DATA"]
        valid_cmd = False

        if self.curr_state("INIT") and input_cmd == "HELO":
            self.handle_helo(msg)
            valid_cmd = True

        if self.curr_state("HELO") and input_cmd == "MAIL FROM:":
            self.handle_mail(msg)
            valid_cmd = True

        if self.curr_state("MAIL") and input_cmd == "RCPT TO:":
            self.handle_rcpt(msg)
            valid_cmd = True
        elif self.curr_state("RCPT") and input_cmd == "RCPT TO:":
            self.handle_rcpt(msg)
            valid_cmd = True

        if self.curr_state("RCPT") and input_cmd == "DATA":
            self.handle_data(msg)
            valid_cmd = True

        if self.curr_state("DATA") and msg != ".":
            self.text_body += "{}\n".format(msg)
            valid_cmd = True

        if self.curr_state("DATA") and msg == ".":
            self.send_ok("FIN")
            self.process_mailbox()
            self.next_mail()
            valid_cmd = True

        if not valid_cmd:
            if self.curr_state("HELO") and input_cmd == "HELO":
                self.send_error("duplicate_helo")
            elif self.curr_state("MAIL") and input_cmd == "MAIL FROM:":
                self.send_error("nested_mail")
            elif input_cmd in cmd_list:
                self.send_error("order")
            else:
                self.send_error("unrecognized")

    # handle HELO command
    def handle_helo(self, msg):
        args = msg.strip().split(" ")
        if len(args) != 2:
            self.send_error("syntax_helo")
        else:
            self.client_name = args[1] if len(args) > 1 else ""
            self.send_ok("HELO")

    # handle MAIL FROM command
    def handle_mail(self, msg):
        args = msg.strip().split(" ")
        valid_syntax = False

        if len(args) == 3 and \
            args[0].upper() == "MAIL" and args[1].upper() == "FROM:":
            valid_syntax = True

        if valid_syntax and self.valid_mail(args[2]):
            self.from_mail = args[2]
            self.send_ok("MAIL")

        if valid_syntax and not self.valid_mail(args[2]):
            self.from_mail = "".join(args[2:])
            self.send_error("sender")

        if not valid_syntax:
            self.send_error("syntax_from")

    # handle RCPT TO command
    def handle_rcpt(self, msg):
        args = msg.strip().split(" ")
        valid_syntax = False

        if len(args) == 3 and \
            args[0].upper() == "RCPT" and args[1].upper() == "TO:":
            valid_syntax = True

        if valid_syntax and self.valid_mail(args[2]):
            self.to_mails.append(args[2])
            self.send_ok("RCPT")

        if valid_syntax and not self.valid_mail(args[2]):
            self.to_mails.append("".join(args[2:]))
            self.send_error("recipient")

        if not valid_syntax:
            self.send_error("syntax_to")

    # handle DATA command
    def handle_data(self, msg):
        # data is processed inside parse method, only send error/ok here
        # for the 'DATA' message
        if len(msg) != 4:
            self.send_error("syntax_data")
        else:
            self.send_ok("DATA")

    def curr_state(self, state):
        if self.states[self.s_pointer] == state:
            return True
        return False

    def process_mailbox(self):
        with self.mailbox_lock:
            self.mail_box = open("mailbox", "a+")
            self.mail_box.write(self.format_text(self.text_body))
            self.mail_box.close()

            if self.count_msg > 0 and self.count_msg % 32 == 0:
                backup = "mailbox.{}-{}".format(self.text_body-32,
                                                     self.text_body)
                copy("mailbox", backup)
                self.mail_box = open("mailbox", "w+")
                self.mail_box.close()

    def next_mail(self):
        self.s_pointer = self.states.index("HELO")
        self.text_body = ""
        self.from_mail = ""
        self.to_mails = []

    def format_text(self, raw_text):
        # for formatting the backup/mailbox
        formatted = "Received: from {} by gk256 (CS4410MP3)\n"\
                    "Number: {}\n"\
                    "From: {}\n".format(self.client_name,
                                        self.count_msg,
                                        self.from_mail)
        for m in self.to_mails:
            formatted += "To: {}\n".format(m)
        formatted += "\n{}\n".format(raw_text)
        return formatted

    def send_ok(self, curr):
        if curr == FINISH:
            self.count_msg += 1
            self.s_pointer = len(self.states)-1
            msg = "250 OK: Delivered {} messages".format(self.count_msg)

        elif curr in self.states[:-1]:
            self.s_pointer = self.states.index(curr)
            msg = OK[curr]
        else:
            self.s_pointer = len(self.states)-1
            msg = "State not recognized"

        self.socket.send(msg)
        self.socket.settimeout(self.TIMEOUT)  # valid commmand resets timeout

    def send_error(self, etype):
        REQUIRE_ARGS = ["order", "sender", "recipient"]
        valid_etype = True

        if etype not in ERROR:
            msg = "Error type not recognized"
            valid_etype = False

        if valid_etype:
            if etype not in REQUIRE_ARGS:
                msg = ERROR[etype]
            if etype == REQUIRE_ARGS[0]:
                msg = ERROR[etype].format(self.states[self.s_pointer+1])
            if etype == REQUIRE_ARGS[1]:
                msg = ERROR[etype].format(self.from_mail)
            if etype == REQUIRE_ARGS[2]:
                msg = ERROR[etype].format(self.to_mails.pop())

        # error command will set the new timeout
        # self.socket.settimeout(self.socket.gettimeout()/2)
        self.socket.send(msg)

    # http://stackoverflow.com/questions/8022530/python-check-for-valid-email-address
    def valid_mail(self, email):
        return not not re.match("[^@]+@[^@]+\.[^@]+", email)

    def run(self):
        # producer
        while True:
            try:
                self.socket = self.pool.get_connection()
                self.handle()
            except socket.timeout:
                self.send_error("timeout")
                self.socket.close()


# thread pool
class ThreadPool:
    def __init__(self, n_threads):
        self.pool_lock = Lock()
        self.conn_available = Condition(self.pool_lock)
        self.request_available = Condition(self.pool_lock)

        self.conn_pool = []  # thread pool
        self.n_connected = 0
        self.max_conn = n_threads

    # producer
    def connection_ready(self, socket):
        with self.pool_lock:
            while self.n_connected >= self.max_conn:
                self.conn_available.wait()
            self.conn_pool.append(socket)
            self.n_connected += 1
            self.request_available.notifyAll()

    # consumer
    def get_connection(self):
        with self.pool_lock:
            while self.n_connected == 0:
                self.request_available.wait()
            socket = self.conn_pool.pop()
            self.n_connected -= 1
            self.conn_available.notifyAll()
            return socket

# the main server loop
def serverloop():
    # init thread pool
    pool = ThreadPool(32)

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # mark the socket so we can rebind quickly to this port number
    # after the socket is closed
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind the socket to the local loopback IP address and special port
    serversocket.bind((host, port))
    # start listening with a backlog of 5 connections
    serversocket.listen(5)

    for _ in range(32):
        ConnectionHandler(pool).start()

    while True:
        # accept a connection
        (clientsocket, address) = serversocket.accept()
        pool.connection_ready(clientsocket)

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
