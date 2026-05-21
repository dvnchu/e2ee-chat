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
        user_sync = clientSck.recv(1024)
        pack_sync = parse_json(user_sync)

        if not pack_sync:
            print("Conexion rechazada: Paquete invalido o vacio")
            clientSck.close()
            return

        user = pack_sync["sender"]

        with users_lock:
            if pack_sync["sender"] in users:
                print(f"Rechazando conexion: {user} ya esta conectado")
                error_pack = create_pack(
                    "error", "SERVER", message="User already connected"
                )
                clientSck.sendall(error_pack)
                clientSck.close()
                return

            users[user] = clientSck
            print(f"Usuario {user} conectado.")

            ok_pack = create_pack(
                "login_success", "server", message="Welcome to the chat"
            )
            clientSck.sendall(ok_pack)
        while True:
            raw_data = clientSck.recv(1024)
            if not raw_data:
                print("El usuario envio un paquete vacio")
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
                    print(f"Usuario {user} desconectado, y limpieza realizada")
        clientSck.close()


def route_msg(message, sender):
    message_pack = parse_json(message)

    if not message_pack:
        print("Ignorando paquete malformado.")
        return

    target = message_pack["target"]
    content = message_pack["content"]

    with users_lock:
        target_sck = users.pop(target, None)

    if target_sck:
        pack = create_pack("chat_msg", sender, target=target, content=content)
        target_sck.sendall(pack)


with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as listeningSck:
    listeningSck.bind((HOST, PORT))
    listeningSck.listen()
    while True:
        clientSck, clientAdd = listeningSck.accept()
        threading.Thread(target=handler, args=(clientSck,), daemon=True).start()
