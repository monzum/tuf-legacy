"""
<Program Name>
  test_libnit_listener.py

<Purpose>
  The purpose of this test is to ensure that the libnit listener is 
  functioning properly. We test this by opening up a simple connection,
  sending and receiving some data. Note that In order to run this, 
"""

import socket


def main():
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_sock.connect(("127.0.0.1",12345))

    test_sock.send("HelloWorld!")
    received_msg = test_sock.recv(1024)

    print "Message received is: " + received_msg
    test_sock.close()

    test_fd = open("HelloWorld.txt",'w')
    test_fd.close()



if __name__ == '__main__':
    main()
