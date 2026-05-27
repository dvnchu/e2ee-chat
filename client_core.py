import base64
import socket
import threading

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey

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
            target=self._get_message, daemon=True
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
                type = pack.get("type")
                if type != "login" & type != "login_success":
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
            type = pack.get("type")

            if type == "error":
                failed_target = pack.get("target")
                text = pack.get("content")
                with self.lock:
                    if failed_target in self.chats:
                        del self.chats[failed_target]
                if self.on_message:
                    self.on_message(f"[ERROR DEL SERVIDOR]: {text}")
                return

            if type == "handshake":
                rsa_signature = base64.b64decode(pack.get("signature"))
                rsa_key_bytes = base64.b64decode(pack.get("public_rsa_key"))
                dh_key_bytes = base64.b64decode(pack.get("public_dh_key"))

                rsa_key = serialization.load_pem_public_key(rsa_key_bytes)

                try:                    
                    rsa_key.verify(
                        rsa_signature,
                        dh_key_bytes,
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH,
                        ),
                        hashes.SHA256(),
                    )
                except InvalidSignature:
                    self.on_message(f"[SECURITY]: Handshake rejected, invalid signature from {sender}")
                    del self.chats[sender]
                    return
                
                with self.lock:
                    sender = pack.get("sender") 
                    if sender not in self.chats:
                        chat = ChatSession(sender)
                        self.chats[sender] = chat
                        self._init_handshake(chat)               
                    
                dh_key = X25519PublicKey.from_public_bytes(dh_key_bytes)
                chat.create_shared_secret(dh_key)
                return

            if type == "chat_msg":
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
            dh_key = session.get_public_key()
            signature = self.private_key.sign(
                dh_key,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            pack = create_pack(
                "handshake",
                self.username,
                target=session.target_user,
                public_dh_key=base64.b64encode(dh_key).decode(),
                public_rsa_key=self.export_rsa_key(),
                signature=base64.b64encode(signature).decode(),
            )
            self.sv_socket.sendall(pack)
        except Exception as e:
            if self.on_message:
                self.on_message(f"[error al realizar el handshake]: {e}")

    def export_rsa_key(self):
        if self._RSA_private_key is None:
            return None
        public_key = self._RSA_private_key.public_key()
        serialized_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return base64.b64encode(serialized_key).decode()
