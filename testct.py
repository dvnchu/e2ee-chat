import socket

HOST = '127.0.0.1'
PORT = 50007

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
    sck.connect((HOST,PORT))
    sck.sendall(b'Hello, world')
    data = sck.recv(1024)
print('Received', repr(data))
