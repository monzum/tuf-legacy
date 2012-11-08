import time
import socket

sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_fd.bind(('127.0.0.1', 12345))
sock_fd.listen(1)
conn, addr = sock_fd.accept()

while True:
	data = conn.recv(1024)
	if not data:
		break
	conn.send(data)
conn.close()
    #time.sleep(1)
