from client_core import ChatClientCore

def on_msg(msg):
    print(f"[A received]: {msg}")

client = ChatClientCore("alice", on_msg, "localhost", 50007)
client.connect()
client._send_message("bob", "hola bob")
input()