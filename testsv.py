import socket
import threading

HOST = ''
PORT = 50007

users = {}
users_lock = threading.Lock()

def handler(clientSck):
        chat = clientSck.recv(1024).decode('utf-8')
        parts = chat.split('|')
        sender = parts[0]
        receiver = parts[1]
        with users_lock:
            users[sender] = clientSck
            print(f"Usuario {sender} conectado.")
        try:
            while True:
                data = clientSck.recv(1024)
                if not data: break
                users[receiver].send(data)
        finally:
            with users_lock:
                if sender in users:
                    del users[sender]
                print(f"Usuario {sender} desconectado")


with socket.socket(family = socket.AF_INET, type=socket.SOCK_STREAM) as listeningSck:
    listeningSck.bind((HOST, PORT))
    listeningSck.listen()
    while True:
        clientSck, clientAdd = listeningSck.accept()
        threading.Thread(target=handler, args=(clientSck,), daemon=True).start()


