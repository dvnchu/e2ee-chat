import os

from client_core import ChatClientCore

motor = ChatClientCore("anna", print, "127.0.0.1", 5050)
motor.connect()

while True:
    comando = input("\n >")
    if comando.startswith("/chat "):
        target = comando.split(" ")[1]
        os.system("clear")

        print(f"=== Sala con {target} ===")
        print(motor._get_message())

        nuevo_msg = input("Mensaje: ")
        motor._send_message(target, nuevo_msg)
