import socket
import threading

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from session import ChatSession
from utils import create_pack, parse_json


class ChatClientCore:
    def __init__(self, username, on_message, ip, port):
        self.username = username
        self.on_message = on_message
        self.chats = {}
        self.sv_ip = ip
        self.sv_port = port
        self.sv_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.lock = threading.Lock()
        self._RSA_private_key = None

    @property
    def private_key(self):
        if self._private_key is None:
            self.on_message("[SYSTEM]: Generating cryptographic keys. Please wait")
            self._private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048
            )
            self.on_message("[SYSTEM]: Successful key generation")
        return self._private_key

    def connect(self):
        self.sv_socket.connect((self.sv_ip, self.sv_port))
        sync = create_pack("login", self.username)
        self.sv_socket.sendall(sync)
        raw_ack = self.sv_socket.recv(1024)
        ack = parse_json(raw_ack)
        if ack and ack.get("type") == "login_success":
            self.on_message(ack.get("content"))

        threading.Thread(
            target=self._get_message, args=(self.sv_socket,), daemon=True
        ).start()

    def _get_message(self):
        try:
            while True:
                data = self.sv_socket.recv(1024)
                if not data:
                    break
                pack = parse_json(data)
                if pack is None:
                    break
                self._route_msg(pack)
        except Exception as e:
            self.on_message(f"[error de red]: {e}")
        finally:
            self.sv_socket.close()

    def _send_message(self, target, text):
        try:
            with self.lock:
                if target not in self.chats:
                    new_chat = ChatSession(target)
                    self.chats[target] = new_chat
                    self._init_handshake(new_chat)
            pack = create_pack("chat_msg", self.username, target=target, content=text)
            self.sv_socket.sendall(pack)
        except Exception as e:
            if self.on_message:
                self.on_message(f"[network error]:{e}")

    def _route_msg(self, pack):
        if not pack:
            return
        try:
            sender = pack.get("sender")
            text = pack.get("content")

            if not sender:
                return

            if sender == "server":
                if self.on_message:
                    self.on_message(f"[SERVER]: {text}")
                    return

            with self.lock:  # Lock para que no consulten varios threads a la vez
                sender_chat = self.chats[sender]
                sender_chat.add_message(sender, text)

            if self.on_message:
                self.on_message(pack)

        except Exception as e:
            if self.on_message:
                self.on_message(f"[error al guardar el mensaje]: {e}")

    def _init_handshake(self, session):
        try:
            key = session.get_public_key()
            signature = self.private_key.sign(
                key,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            pack = create_pack(
                "handshake",
                self.username,
                target=session.target,
                public_key=key,
                signature=signature,
            )
            self.sv_socket.sendall(pack)
            session.create_shared_secret()
        except Exception as e:
            if self.on_message:
                self.on_message(f"[error al realizar el handshake]: {e}")
