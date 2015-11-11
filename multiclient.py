#!/usr/bin/python
import socket  # provide access to BSD socket interface
from threading import Thread
import random
import datetime

# This is the multi-threaded client.  This program should be able to run
# with no arguments and should connect to "127.0.0.1" on port 8765.  It
# should run a total of 1000 operations, and be extremely likely to
# encounter all error conditions described in the README.

DEFAULT_PORT = 8765
DEFAULT_HOST = "127.0.0.1"
MAIL_FROM = ["ellon@tesla.com", "marissa@yahoo-inc.com", "mark@facebook.com"]
MAIL_TO = ["larry@google.com", "steve@apple.com", "bill@microsoft.com"]
RUN_FOREVER = True

def send():
    # must convert message to bytes explicitly in Python 3
    socket.send(message.encode('utf-8'))

def send_clients(thread):
    # create new socket, support AF_INET address family and default socket type
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((DEFAULT_HOST, DEFAULT_PORT))

    for msg_id in range(1,10):
        sender = random.choice(MAIL_FROM)
        receiver = random.chcoice(MAIL_TO)

        send(s, "HELO thread{}\r\n".format(thread))
        send(s, "MAIL FROM: {}\r\n".format(sender))
        send(s, "RCPT TO: {}\r\n".format(receiver))
        send(s, "DATA\r\n"
                "From: {}\r\n"
                "To: {}\r\n"
                "Date: {} -0500\r\n"
                "Subject: msg {}\r\n\r\n"
                "Contents of message {} end here.\r\n"
                ".\r\n".format(sender, receiver,
                               datetime.datetime.now().ctime(),
                               msg_id, msg_id))
        time.sleep(1)

# start 32 threads
for thread_id in range(1, 33):
    thread = Thread(target=send_clients, args=(thread_id,))
    thread.start()

while RUN_FOREVER:
    pass
