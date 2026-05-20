from datetime import datetime

class ChatSession:
    def __init__(self, target_user):
        self.target_user = target_user
        self.shared_key = None
        self.history = []
        self.is_secure = False

    def add_message(self, sender, text):
        timestamp = datetime.now().strftime("%H:%M")
        formatted_msg = f"[{timestamp}] {sender}: {text}]"
        self.history.append(formatted_msg)

    def get_history(self):
        return  "\n".join(self.history)
