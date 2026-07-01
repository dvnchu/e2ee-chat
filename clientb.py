from client_core import ChatClientCore

def on_msg(msg):
    print(f"[B received]: {msg}")

client = ChatClientCore("bob", on_msg, "localhost", 50007)
client.connect()
input()