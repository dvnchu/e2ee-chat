import socket
import threading
import json
import server
from utils import parse_json, create_pack

HOST = '127.0.0.1'
PORT = 50007
USER = input("Register with username:")


def sendmsg(serverSck):
    while True:
        data = input().split(':')
        message = create_pack("chat_msg", USER, target=data[0], content=data[1])
        if data == "exit": break
        serverSck.sendall(message)

def receivemsg(serverSck):
    try:
        while True:
            raw_data = serverSck.recv(1024)

            if not raw_data:
                print("\nConexion cerrrada por el servidor.")
                break

            pack = parse_json(raw_data)

            if pack is None:
                print("\nSe recibie un paquete corrupto. Abortando")
                break

            sender = pack["sender"]
            content = pack["content"]
            print(f"\n{sender}: {content}")
    except Exception as e:
        print(f"\nError inesperado en recepcion: {e}")
    finally:
        serverSck.close()
    print("Recursos de red liberados.")


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
    sck.connect((HOST,PORT))
    sck.sendall(USER.encode('utf-8'))
    threading.Thread(target = receivemsg, args=(sck,)).start()
    sendmsg(sck)


