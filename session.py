from datetime import datetime

from cryptography.hazmat.primitives.asymmetric import x25519


class ChatSession:
    def __init__(self, target_user):
        self.target_user = target_user
        self._dh_private_key = x25519.X25519PrivateKey.generate()
        self.shared_secret = None
        self.history = []
        self.is_secure = False
        self.state = "PENDING"
        self.queue = []

    def get_public_key(self):
        return self._dh_private_key.public_key().public_bytes_raw()

    def create_shared_secret(self, peer_public_key):
        self.shared_secret = self._dh_private_key.exchange(peer_public_key)

    def add_message(self, sender, text):
        timestamp = datetime.now().strftime("%H:%M")
        formatted_msg = f"[{timestamp}] {sender}: {text}"
        self.history.append(formatted_msg)

    def get_history(self):
        return "\n".join(self.history)
