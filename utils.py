import json
from datetime import datetime, timezone


def parse_json(data):
    try:
        data_string = data.decode("utf-8")
        pack = json.loads(data_string)
        return pack
    except json.JSONDecodeError:
        print("Error: El paquete recibido no es un JSON válido")
        return None
    except UnicodeDecodeError:
        print("Error: No se pudo decodificar el formato de texto")
        return None


def create_pack(msg_type, sender, **kwargs):
    pack = {
        "type": msg_type,
        "sender": sender,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    match msg_type:
        case "login":
            pack["content"] = "sync_request"
        case "login_success":
            pack["content"] = kwargs.get("message")
        case "chat_msg":
            pack.update(
                {"target": kwargs.get("target"), "content": kwargs.get("content")}
            )
        case "error":
            pack["content"] = kwargs.get("error_msg")
        case "handshake":
            pack.update(
                {
                    "target": kwargs.get("target"),
                    "public_dh_key": kwargs.get("public_dh_key"),
                    "public_rsa_key": kwargs.get("public_rsa_key"),
                    "signature": kwargs.get("signature"),
                }
            )
        case _:
            return b""

    return json.dumps(pack).encode("utf-8")
