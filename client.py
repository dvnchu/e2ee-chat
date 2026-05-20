import socket
import threading
from utils import parse_json, create_pack
from session import ChatSession

HOST = '127.67.67.1'
PORT = 50007
USER = input("Register with username:")

chats = {}

def sendmsg(serverSck):
    while True:
        msg_input = input("\nTARGET:MESSAGE: ")
        data = msg_input.split(':')
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
    sync_pack = create_pack("login", USER)
    sck.sendall(sync_pack)
    print("Esperando confirmación del servidor...")
    raw_ack = sck.recv(1024)
    ack_pack = parse_json(raw_ack)
    if ack_pack and ack_pack.get("type") == "login_success":
        print(ack_pack.get('content'))

    input("\n>")
    threading.Thread(target = receivemsg, args=(sck,)).start()
    sendmsg(sck)


