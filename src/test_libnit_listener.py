import random
import libnit_listener
from network_call_processor import NetworkCallProcessor


# Define a test processor that generates a random socket fd.
# The processor will return 0 if the socket fd matches, otherwise
# it will return an error.
class TestProcessor(NetworkCallProcessor):

    # Describe a bad error code.
    EBADF = 9

    def __init__(self):
        NetworkCallProcessor.__init__(self)
        self.random_sock_fd = int(5000 + (random.random() * 1000))

    def call_socket(self, domain, sock_type):
        print "Created sockfd:", self.random_sock_fd
        return (self.random_sock_fd, -1)

    def call_connect(self, sockfd, conn_ip, conn_port):
        print "Received sockfd:", sockfd
        if int(sockfd) == self.random_sock_fd:
            return (0, -1)
        else :
            return (None, self.EBADF)

    def call_send(self, sockfd, msg, flags):
        if int(sockfd) == self.random_sock_fd:
            self.send_msg = msg
            return (len(msg), -1)
        else :
            return (None, self.EBADF)

    def call_recv(self, sockfd, msg_len, flags):
        if int(sockfd) == self.random_sock_fd:
            return (self.send_msg, -1)
        else :
            return (None, self.EBADF)

    def call_close(self, sockfd):
        if int(sockfd) == self.random_sock_fd:
            return (0, -1)
        else :
            return (None, self.EBADF)




def main():
    """
    <Purpose>
      Launch a simple LibnitListener with the defined test processor
      above.
    """

    simple_processor = TestProcessor()
    
    new_listener = libnit_listener.LibnitListener(simple_processor)
    
    new_listener.serve_forever()


if __name__ == '__main__':
    main()
