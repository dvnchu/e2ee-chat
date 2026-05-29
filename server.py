import socket
import threading

from utils import create_pack, parse_json

HOST = ""
PORT = 50007

users = {}
users_lock = threading.Lock()


def handler(clientSck):
    user = None
    try:
        user_sync = clientSck.recv(4096)
        pack_sync = parse_json(user_sync)

        if not pack_sync:
            print("Connection rejected: Invalid package")
            clientSck.close()
            return

        user = pack_sync["sender"]

        with users_lock:
            if pack_sync["sender"] in users:
                print(f"Rejecting connection: {user} is already connected")
                error_pack = create_pack(
                    "error", "SERVER", message="User already connected"
                )
                clientSck.sendall(error_pack)
                clientSck.close()
                return

            users[user] = clientSck
            print(f"User {user} connected.")

            ok_pack = create_pack(
                "login_success", "server", content="Welcome to the chat"
            )
            clientSck.sendall(ok_pack)
        while True:
            raw_data = clientSck.recv(4096)
            if not raw_data:
                print("User sent an empty package")
                clientSck.close()
                return
            route_msg(raw_data, user)
    except Exception as e:
        print(f"Error en el handler: {e}")
    finally:
        with users_lock:
            if user:
                with users_lock:
                    users.pop(user, None)
                    print(f"User {user} disconnected")
        clientSck.close()


def route_msg(pack, sender):
    parsed_pack = parse_json(pack)
    if not parsed_pack:
        print("Ignorando paquete malformado.")
        return

    target = parsed_pack.get("target")
    msg_type = parsed_pack.get("msg_type")


    with users_lock:
        target_sck = users.get(target)

    if not target_sck:
        with users_lock:
            sender_sck = users.get(sender)
            error_pack = create_pack("error", "server", content="User not found")
            sender_sck.sendall(error_pack)
        return 
    
    print(parsed_pack.get("content"))
    target_sck.sendall(pack)
   

with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as listeningSck:
    listeningSck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listeningSck.bind((HOST, PORT))
    listeningSck.listen()
    while True:
        clientSck, clientAdd = listeningSck.accept()
        threading.Thread(target=handler, args=(clientSck,), daemon=True).start()
