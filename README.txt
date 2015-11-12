CS4410 MP3:  SMTP Server
========================

Email is the backbone of modern-day communication.  In this assignment you will
be building a multi-threaded mail server that supports basic features of the
SMTP mail transfer protocol.  Along the way you'll get a taste of
socket-oriented network programming.

For sake of simplification, you will build a mail server which simply accepts
email for local delivery and appends the email to a single local inbox.
Despite its limited functionality, your server must be able to support many
concurrent clients without allowing any single client to impact any other
client.

We've provided you with a bare-bones SMTP server to get you started.  The
bare-bones server accepts connections on port 8765 and immediately closes each
connection without any data transfer.  You will start with this bare-bones
structure and implement a multi-threaded server that supports mail delivery.

The bare-bones server handles requests sequentially.  While this simplifies
implementation, it does not allow for concurrent requests.  Your first task in
this assignment is to change the server so that each incoming connection is
passed off to a *thread pool*.  Thread pools are a textbook example of a
producer consumer relationship.  The single main thread acts as the producer of
incoming connections, while a constant number of threads (collectively called
the pool) act as a set of consumers.

Your thread pool implementation must only rely on synchronization primitives
from Python's threading library (Thread, Lock, Semaphore, Condition).  Notably,
you *must not* use Python's thread-safe queue module or its multiprocessing
module.

Our bare-bones server does not support mail delivery at all.  Each incoming
connection is immediately closed.  Your implementation must support a
simplified SMTP protocol.  Here's a typical interaction between a client and
server in which the client sends mail from student@CS4410 to TA@CS4410:

    +---------------------------------------+-------------------------------+
    | Server                                | Client                        |
    +---------------------------------------+-------------------------------+
    | 220 netid SMTP CS4410MP3              |                               |
    |                                       | HELO client                   |
    | 250 netid                             |                               |
    |                                       | MAIL FROM: student@CS4410     |
    | 250 OK                                |                               |
    |                                       | RCPT TO: TA@CS4410            |
    | 250 OK                                |                               |
    |                                       | DATA                          |
    | 354 End data with <CR><LF>.<CR><LF>   |                               |
    |                                       | I made an awesome submission! |
    |                                       | Network programming is fun.   |
    |                                       | .                             |
    | 250 OK:  delivered message 1          |                               |
    +---------------------------------------+-------------------------------+

SMTP is a line-oriented protocol.  Although it is not shown in the previous
exchange, each line ends with the special carriage-return/line-feed combination
'\r\n'.  Notice that with the exception of the message body, each line triggers
a response from the server.  The special number codes begin each line from the
server and provide feedback to clients about the success and failure of each
command.

The numbers that precede the responses from the server are status codes. By
convention, numbers in the 200-299 range indicate that acceptable progression
through mail delivery. Numbers in the 500-599 range indicate errors, 400-499
indicate timeouts, and 300-399 indicate alert conditions (such as the mail
server changing its input collection mode such that it is now seeking input
until a "<CR><LF>.<CR><LF>" marker). When picking response codes, you must
follow the conventions as indicated in various parts of this document (e.g.
220 for the first message, 421 for timeouts, 354 for the response to a
successful DATA message, etc).

SMTP is intended to be human-readable, and it used to be the case that people
would regularly send emails by hand.  As such, the protocol is very tolerant of
errors.  In the event of an error, the server delivers a message, *but does not
prevent future commands from succeeding*.   There are several error cases we
expect you to gracefully handle:

 - Recognized commands that do not obey the syntax we've described should
   receive a response of:

        501 Syntax:  proper syntax

 - Commands must come in the order HELO, MAIL FROM, RCPT TO, DATA.
   Recognized commands that come out of order must cause a response of:

        503 Error: need XXX command

 - Unrecognized commands should receive a response of:

        500 Error: command not recognized

 - A client may only send one valid HELO command during an entire connection.
   Any subsequent HELO commands that are otherwise valid must instead cause a
   response of:

        503 Error: duplicate HELO

 - A client may only send one valid MAIL FROM command per message. Any
   subsequent MAIL FROM commands that are otherwise valid must instead cause a
   response of:

        503 Error: nested MAIL command

 - For simplification, we consider any email address that consists of
   consecutive, printable ASCII characters to be valid.  If an email provided
   as an argument to MAIL FROM contains whitespace (ignore leading or trailing
   whitespace) your implementation should return:

        555 <bad email>: Sender address rejected

   Similarly, if an email provided as an argument to RCPT TO contains
   significant whitespace, your implementation should return:

        555 <bad email>: Recipient address invalid

 - If a client goes dormant, your code should properly timeout and close the
   connection.  For this project, we define a client to be dormant if it does
   not send a command for more than 10 seconds (during the command phase), or
   does not send data for more than 10 seconds (during the data phase).  When
   closing the connection with a dormant client, send the error code:

        421 4.4.2 netid Error: timeout exceeded

 - If a client does not successfully complete a command within 10
   seconds, your code should timeout and close the connection. Note that
   a client that continually provides invalid commands should not be able
   to continue communicating with the server indefinitely. When closing
   the connection with a client that is too slow, is dormant, or is
   continually sending invalid commands, send the error code:

        421 4.4.2 netid Error: timeout exceeded

As mentioned previously, sending an error message does not terminate
communication.  Below we show an example SMTP conversations which almost
succeeds despite being interrupted with errors.

    +-----------------------------------------+-----------------------------+
    | Server                                  | Client                      |
    +-----------------------------------------+-----------------------------+
    | 220 netid SMTP CS4410MP3                |                             |
    |                                         | HELO                        |
    | 501 Syntax:  HELO yourhostname          |                             |
    |                                         | HELO clienthostname         |
    | 250 netid                               |                             |
    |                                         | mkdir                       |
    | 500 Error: command not recognized       |                             |
    |                                         | MAIL FROM: student @CS4410  |
    | 555 <student @CS4410>: Sender address rejected                        |
    |                                         | MAIL FROM: student@CS4410   |
    | 250 OK                                  |                             |
    |                                         | MAIL FROM: professor@CS4410 |
    | 503 Error: nested MAIL command          |                             |
    |                                         | RCPT TO: TA @CS4410         |
    | 555 <TA @CS4410>: Recipient address invalid                           |
    |                                         | RCPT TO: TA@CS4410          |
    | 250 OK                                  |                             |
    |                                         | DATA                        |
    | 354 End data with <CR><LF>.<CR><LF>     |                             |
    |                                         | I'm going to send and wait  |
    | 421 4.4.2 netid Error: timeout exceeded |                             |
    +-----------------------------------------+-----------------------------+

Had the client sent a trailing "." before the timeout, this message would have
been successfully delivered despite encountering every error response your
basic SMTP server must generate.

Email should be saved on disk in a file named `mailbox`.  When we launch your
SMTP server, it should create this file in the current directory, erasing all
current contents.  Each email should be appended to this file in a way that
preserves the integrity and order of the emails.  For example, if the emails
from the previous two examples were both delivered, the resulting `mailbox`
file should be:

    +-----------------------------------------------------------------------+
    | Received: from client by netid (CS4410MP3)                            |
    | Number: 1                                                             |
    | From: student@CS4410                                                  |
    | To: TA@CS4410                                                         |
    |                                                                       |
    | I made an awesome submission!                                         |
    | Network programming is fun.                                           |
    |                                                                       |
    | Received: from clienthostname by netid (CS4410MP3)                    |
    | Number: 2                                                             |
    | From: student@CS4410                                                  |
    | To: TA@CS4410                                                         |
    |                                                                       |
    | I'm going to send and wait                                            |
    |                                                                       |
    +-----------------------------------------------------------------------+

A client may send multiple RCPT TO commands during a single message. Doing so
will cause a message to be delivered once (and be assigned a single message ID)
and appear once in the mailbox, with multiple "To:" lines in the same mssage.

You can test your server by connecting to it with a telnet client.  To do so,
run your server on a linux machine, and on the same machine run "telnet
localhost 8765" (or whatever port your server is currently listening on).

Once you have a functioning client and server, you should modify our provided
client to thoroughly test your server program.  As part of this modification,
you should create a version called 'multiclient.py' which opens 32 connections
at once, and psuedorandomly generates SMTP commands.  An implementation which
is eligible for full credit will randomly vary the client-provided information
(hostnames, emails, and data) and will follow the core protocol in the normal
case.  To test error conditions, 'multiclient.py' should randomly decide to
deviate from the protocol and issue a command that results in an error.  It
should be able to detect that your server sends the appropriate response.
Please see the included 'multiclient.py' skeleton for more information.

Here are some things you should keep in mind as you build your SMTP server:
 - Your thread pool should contain 32 threads.
 - Each thread should finish one connection before moving on to the next.
 - The producer (which calls accept on the listening socket) should not accept
   connections at a faster rate than the thread pool is processing them.  It is
   better to let them become backlogged in the OS than to accept them and let
   them sit on a queue.  Your implementation must behave in this fashion.
 - Emails should be assigned a unique number, indicating their order of
   delivery.  This number should reflect the order of the emails in the
   mailbox.  For consistency, the first message is always 1, and every
   subsequent message is <number of previously delivered message> + 1.
 - You'll need to build at least one monitor to enable your multi-threaded
   behavior to adhere to our spec.  Servers which do not implement proper
   monitors will not receive full credit.
 - We will test on the Linux networking stack using Python 2.7.  Although
   Windows provides a sockets API that Python wraps quite nicely, Python does
   not do anything to smooth over compatibility issues stemming from Windows
   not being Linux.  It is almost guaranteed that code developed exclusively
   for Windows will not work on Linux without a little effort.  Please be aware
   of this before you submit.
 - It is perfectly acceptable, and encouraged, to cross-test your SMTP server
   with other students.  The procedure for doing so is to both log into the
   CSUGLab machines and spawn your server on a port that is known to both you
   and others.  At no time should you be in possesion of, or have access to,
   the source code of another student.

Mailbox Backup
------------

Create a separate "backup" thread whose job is to create a backup of the
mailbox.  Creating a backup involves copying the current `mailbox` file to a
separate location, and emptying `mailbox`.  Messages should be backed up in
groups of 32.  For instance, upon delivering message number 64, the backup
thread will create file `mailbox.33-64`, and then truncate `mailbox`.  After
this thread completes, the current directory will contain the files
`mailbox`, `mailbox.1-32`, and `mailbox.33-64`.

The backup process should not be affected if another thread tries to deliver a
message.  The thread that tries to deliver a new message will wait for the
backup process to complete before writing its message.

Submission Instructions
-----------------------

Your submission should include at least the following files (named in exactly
this fashion):

README.txt:
    A plain-text, ASCII file containing your netid, and a description of all
    problems you know about that exist in your implementation.  As usual, we
    simply use this to save us time, and will give your code the same
    attention that every submission receives.

QUESTIONS.txt:
    A plain-text, ASCII file containing your netid, and answers to every
    question contained in the distributed QUESTIONS.txt.

server.py:
    This should be your server implementation.  If run with no arguments,
    `server.py` should bind to '127.0.0.1' on port 8765.  Messages should be
    saved to the `mailbox` file in the directory in which server.py is
    launched.

multiclient.py:
    This is the multiclient as described in this README.  If run with no
    arguments, `multiclient.py` should connect to '127.0.0.1' on port 8765 and
    begin the stress test.  The stress test should run through every error case
    in the protocol, and possibly other error cases that you yourself conceive.
    Operations should be relatively fast.  We will give 1 minute for all 1,000
    operations, requiring your `multiclient.py` to sustain 17 ops/sec.


You need to submit a zip file, which when unzipped gives a single folder "MP3".
Your source code, README.txt, QUESTIONS.txt and any other relevant files should
be located directly inside this folder.

If you have any questions, do not hesitate to use Piazza or come to Office Hours.
