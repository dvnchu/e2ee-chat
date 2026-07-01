import socket
import threading

from utils import create_pack, parse_json

HOST = ""
PORT = 5050

users = {}
users_lock = threading.Lock()


def handler(clientSck):
    user = None
    socket_file = None
    try:
        socket_file = clientSck.makefile('rb')
        user_sync = socket_file.readline()
        if not user_sync:
            clientSck.close()
            return
            
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
                    "error", "SERVER", content="User already connected"
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
            
        for line in socket_file:
            if not line:
                break
            route_msg(line, user)
    except Exception as e:
        print(f"[ERROR]: Handler exception: {e}")
    finally:
        if socket_file:
            socket_file.close()
        with users_lock:
            if user:
                users.pop(user, None)
                print(f"User {user} disconnected")
        clientSck.close()


def route_msg(pack, sender):
    parsed_pack = parse_json(pack)
    if not parsed_pack:
        print("[WARNING]: Ignoring malformed package.")
        return

    target = parsed_pack.get("target")
    msg_type = parsed_pack.get("msg_type")

    if target == sender:
        with users_lock:
            sender_sck = users.get(sender)
        if sender_sck:
            error_pack = create_pack("error", "server", content="You cannot message yourself")
            sender_sck.sendall(error_pack)
        return


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
