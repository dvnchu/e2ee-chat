import socket
import threading
import json
from datetime import datetime, timezone

HOST = ''
PORT = 50007

users = {}
users_lock = threading.Lock()


def parse_json(data):
    try:
        data_string = data.decode("utf-8")
        pack = json.loads(data_string)

        return pack
    except json.JSONDecodeError:
        print("Error: El paquete recibido no es un JSON válido")
        return None
    except UnicodeDecodeError:
        print("Error: No se pudo decodificar el formato de texto")


def createPack(msg_type, sender, target=None, message=None):
    pack = {
        "type": msg_type,
        "sender": sender,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if msg_type == "login":
        pack["content"] = "sync_request"
    elif msg_type == "chat_msg":
        if not target or not message:
            raise ValueError("chat_msg requires target y message")
        pack["target"] = target
        pack["content"] = message
    else:
        return b"" 
    return json.dumps(pack).encode("utf-8")




def handler(clientSck):
        user_sync = clientSck.recv(1024).decode('utf-8')
        pack_sync = parse_json(user_sync)
        with users_lock:
            if pack_sync and pack_sync["sender"] in users:
                user = pack_sync["sender"]
                print(f"Usuario {user} conectado.")
            else:
                clientSck.
        try:
            while True:
                data = clientSck.recv(1024).decode()
                json.d
                if not data: break
                users[receiver].send(data)
        finally:
            with users_lock:
                if user in users:
                    del users[user]
                print(f"Usuario {user} desconectado")



with socket.socket(family = socket.AF_INET, type=socket.SOCK_STREAM) as listeningSck:
    listeningSck.bind((HOST, PORT))
    listeningSck.listen()
    while True:
        clientSck, clientAdd = listeningSck.accept()
        threading.Thread(target=handler, args=(clientSck,), daemon=True).start()


