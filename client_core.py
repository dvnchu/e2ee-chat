import base64
import socket
import threading
import os
import json
import platform

from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

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
        self.app_dir = self.get_app_dir()
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.key_path = self.app_dir / "private_key.pem"
        self.known_keys_path = self.app_dir / "known_keys.json"
        self.known_keys = self._load_known_keys()
    
      
    @property
    def private_key(self):
        if self._RSA_private_key is None:
            if not self.key_path.exists():
                self.on_message("[SYSTEM]: Generating cryptographic keys. Please wait")
                self._RSA_private_key = rsa.generate_private_key(
                    public_exponent=65537, key_size=2048
                )
                pem_key = self._RSA_private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                with open(self.key_path, "wb") as f:
                    f.write(pem_key)
                self.on_message("[SYSTEM]: Successful key generation")   
                
            with open(self.key_path, "rb") as key_file:
                self._RSA_private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                ) 
        return self._RSA_private_key

    @staticmethod
    def get_app_dir(app_name="e2eechat"):
        system = platform.system()
    
        if system == "Windows":
            return Path.home() / "AppData" / "Local" / app_name
        
        elif system == "Darwin": 
            return Path.home() / "Library" / "Application Support" / app_name
        
        else: 
            return Path.home() / ".local" / "share" / app_name    


    def _load_known_keys(self):
        if self.known_keys_path.exists():
            try:
                with open(self.known_keys_path, "r") as f:
                    return json.load(f) 
            except Exception as e:
                self.on_message(f"[ERROR]: Contact files couldnt be read: {e}")
                return {}
        return {}

    def _save_known_keys(self):
        with self.lock:
            keys_copy = self.known_keys.copy()
        try:
            with open(self.known_keys_path, "w") as f:
                json.dump(keys_copy, f, indent = 4)
        except Exception as e:
            self.on_message(f"[ERROR]: {e}")
                
        
   
    def connect(self):
        self.sv_socket.connect((self.sv_ip, self.sv_port))
        sync = create_pack("login", self.username)
        self.sv_socket.sendall(sync)
        
        self.socket_file = self.sv_socket.makefile('rb')
        
        raw_ack = self.socket_file.readline()
        if raw_ack:
            ack = parse_json(raw_ack)
            if ack and ack.get("type") == "login_success":
                self.on_message(ack.get("content"))

        threading.Thread(
            target=self._get_message, daemon=True
        ).start()

    def _get_message(self):
        try:
            for line in self.socket_file:
                pack = parse_json(line)
                if pack is None:
                    continue
    
                msg_type = pack.get("type")
                if msg_type not in ("login", "login_success"):
                    self._route_msg(pack)
        except Exception as e:
            self.on_message(f"[Network error]: {e}")
        finally:
            if hasattr(self, 'socket_file') and self.socket_file:
                self.socket_file.close()
            self.sv_socket.close()

    def _send_message(self, target, text):
        try:
            with self.lock:
                if target not in self.chats:
                    new_chat = ChatSession(target)
                    self.chats[target] = new_chat
                    self._init_handshake(new_chat)
                
                chat = self.chats[target]
                if chat.shared_secret is None:
                    chat.queue.append(text)
                    if self.on_message:
                        self.on_message(f"[SYSTEM]: Secure session with {target} is pending. Message queued.")
                    return
            
            self._send_encrypted(chat, text)
        except Exception as e:
            if self.on_message:
                self.on_message(f"[network error]: {e}")

    def _send_encrypted(self, chat, text):
        aesgcm = AESGCM(chat.shared_secret)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, text.encode('utf-8'), None)
        encrypted_b64 = base64.b64encode(nonce + ciphertext).decode('utf-8')
        
        pack = create_pack("chat_msg", self.username, target=chat.target_user, content=encrypted_b64)
        self.sv_socket.sendall(pack)

    def _route_msg(self, pack):
        if not pack:
            return
        try:
            sender = pack.get("sender")
            type = pack.get("type")
            text = pack.get("content")
            if type == "error":
                failed_target = pack.get("target")
                with self.lock:
                    self.chats.pop(failed_target, None)
                if self.on_message:
                    self.on_message(f"[SERVER ERROR]: {text}")
                return

            if type == "handshake":
                rsa_signature = base64.b64decode(pack.get("signature"))
                rsa_key_bytes = base64.b64decode(pack.get("public_rsa_key"))
                rsa_key_bytes_b64 = pack.get("public_rsa_key")
                dh_key_bytes = base64.b64decode(pack.get("public_dh_key"))

                rsa_key = serialization.load_pem_public_key(rsa_key_bytes)

                needs_save = False

                with self.lock:
                    if sender not in self.known_keys:
                        self.known_keys[sender] = rsa_key_bytes_b64
                        needs_save = True
                    else:
                        if self.known_keys[sender] != rsa_key_bytes_b64:
                            self.on_message(f"[SECURITY ALERT]: Public key for {sender} changed! Connection aborted.") 
                            return
    
                if needs_save:
                    self._save_known_keys()
                    
                try:                    
                    rsa_key.verify(
                        rsa_signature,
                        dh_key_bytes,
                        padding.PSS( mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH,
                        ),
                        hashes.SHA256(),
                    )
                except InvalidSignature:
                    if self.on_message:
                        self.on_message(f"[SECURITY]: Handshake rejected, invalid signature from {sender}")
                    with self.lock:
                        self.chats.pop(sender, None)
                    return
                
                with self.lock:
                    if sender not in self.chats:
                        chat = ChatSession(sender)
                        self.chats[sender] = chat
                        self._init_handshake(chat)               
                    else:
                        chat = self.chats[sender]
                        
                dh_key = X25519PublicKey.from_public_bytes(dh_key_bytes)
                chat.create_shared_secret(dh_key)

                with self.lock:
                    chat.is_secure = True
                    chat.state = "SECURE"
                    queued_messages = list(chat.queue)
                    chat.queue.clear()
                
                for msg in queued_messages:
                    try:
                        self._send_encrypted(chat, msg)
                    except Exception as e:
                        if self.on_message:
                            self.on_message(f"[network error sending queued message]: {e}")
                return

            if type == "chat_msg":
                with self.lock:
                    if sender in self.chats:
                        sender_chat = self.chats[sender]
                        if sender_chat.shared_secret is not None:
                            try:
                                encrypted_bytes = base64.b64decode(text.encode('utf-8'))
                                nonce = encrypted_bytes[:12]
                                ciphertext = encrypted_bytes[12:]
                                aesgcm = AESGCM(sender_chat.shared_secret)
                                decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
                                decrypted_text = decrypted_bytes.decode('utf-8')
                                sender_chat.add_message(sender, decrypted_text)
                                pack["content"] = decrypted_text
                            except Exception as decrypt_err:
                                if self.on_message:
                                    self.on_message(f"[SECURITY]: Failed to decrypt message from {sender}: {decrypt_err}")
                                return 
                        else:
                            if self.on_message:
                                self.on_message(f"[SYSTEM]: Received message from {sender} but secure session is not established.")
                            return
                    else:
                        if self.on_message:
                            self.on_message(f"[SYSTEM]: Received message from {sender} but no session exists.")
                        return
        
                if self.on_message:
                    self.on_message(pack)
    
        except Exception as e:
            if self.on_message:
                self.on_message(f"[LOCAL ERROR]: Failed to route message: {e}")

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
                self.on_message(f"[LOCAL ERROR]: Failed to initialize handshake: {e}")

    def export_rsa_key(self):
        public_key = self.private_key.public_key()
        serialized_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return base64.b64encode(serialized_key).decode()
