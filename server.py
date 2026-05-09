import socket
import threading

HOST = '0.0.0.0'
PORT = 5000

clients = {}

def handle_client(conn,addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    try:
        username = conn.recv(1024).decode('utf-8')
        clients[username] = conn
        print(f"[REGISTER] {username} is online.")

        while True:
            data = conn.recv(4069).decode('utf-8')
