import time
import socket

sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_fd.bind(('127.0.0.1', 12345))
sock_fd.listen(1)
sock_fd.accept()

while True:
    time.sleep(1)
