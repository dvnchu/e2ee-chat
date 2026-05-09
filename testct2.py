import socket

HOST = '127.0.0.1'
PORT = 50007

msg = input("send msg")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
    sck.connect((HOST,PORT))
    sck.sendall(msg.encode('utf-8'))
    data = sck.recv(1024)
print('received', repr(data))
