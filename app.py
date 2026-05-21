from motor import ChatClientCore
import os

motor = ChatClientCore("anna")

while True:
    comando = input("\n >")
    if comando.startswith("/chat "):
        target = comando.split(" ")[1]
        os.system("clear")

        print(f"=== Sala con {target} ===")
        print(motor.get_messages(target))

        nuevo_msg = input("Mensaje: ")
        motor.send_message(target, nuevo_msg)
