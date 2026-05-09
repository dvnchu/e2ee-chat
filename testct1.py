import socket
import threading

HOST = '127.0.0.1'
PORT = 50007
USER = input("Who are you:")
DESTINATARY = input("Who are you messaging: ")

def sendmsg(serverSck):
    while True:
        data = input("whats the message ")
        if data == "exit": break
        serverSck.sendall(data.encode('utf-8'))

def receivemsg(serverSck):
    while True:
        msg = serverSck.recv(1024)
        print(msg.decode('utf-8'))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
    sck.connect((HOST,PORT))
    chat = f"{USER}|{DESTINATARY}"
    sck.sendall(chat.encode('utf-8'))
    threading.Thread(target = receivemsg, args=(sck,)).start()
    sendmsg(sck)


