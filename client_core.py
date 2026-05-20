import threading
import socket
from utils import create_pack, parse_json

class ChatClient:
    def __init__(self, username, on_message,  ip, port):
        self.username = username
        self.on_message = on_message
        self.chats = {}
        self.sv_ip = ip
        self.sv_port = port 
        self.sv_socket = socket.socket(family = socket.AF_INET, type=socket.SOCK_STREAM)



    def connect(self):
        self.sv_socket.connect((self.sv_ip, self.sv_port))
        sync = create_pack("login", self.username)
        self.sv_socket.sendall(sync)
        raw_ack = self.sv_socket.recv(1024)
        ack = parse_json(raw_ack)
        if(ack and ack.get("type") == "login_success"):
            self.on_message(ack.get("content"))

        threading.Thread(target = self.get_message, args=(self.sv_socket,), daemon=True).start()


    def _get_message(self):
        try:
            while True:
                data = self.sv_socket.recv(1024)
                if not data: break
                pack = parse_json(data)
                if pack is None:
                    break
                self._route_msg(pack)
        except Exception as e:
            self.on_message(f"[error de red]: {e}")
        finally:
            self.sv_socket.close()


    def _send_message(self,target,text):



    def _route_msg(self, pack)


