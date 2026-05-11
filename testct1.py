import socket
import threading
import json
from datetime import datetime, timezone

HOST = '127.0.0.1'
PORT = 50007
USER = input("Register with email:")

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


def sendmsg(serverSck):
    while True:
        data = input().split(':')
        message = createPack("chat_msg", USER, data[0], data[1])
        if data == "exit": break
        serverSck.sendall(message)

def receivemsg(serverSck):
    while True:
        msg = serverSck.recv(1024)
        print("\n", f"{USER}:{msg.decode('utf-8')}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
    sck.connect((HOST,PORT))
    sck.sendall(USER.encode('utf-8'))
    threading.Thread(target = receivemsg, args=(sck,)).start()
    sendmsg(sck)


