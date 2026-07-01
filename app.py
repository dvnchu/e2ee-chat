

import sys
from datetime import datetime

from prompt_toolkit import Application
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, FloatContainer, Float
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style

from client_core import ChatClientCore


STYLE = Style.from_dict({

    "status":            "bg:#1a1a2e #e0e0e0",
    "status.key":        "bg:#1a1a2e #7c83ff bold",
    "status.secure":     "bg:#1a1a2e #50fa7b bold",
    "status.warning":    "bg:#1a1a2e #ffb86c bold",

    "tab":               "bg:#16213e #8892b0",
    "tab.active":        "bg:#2a2a4a #7c83ff bold",
    "tab.unread":        "bg:#16213e #ff5555 bold",
    "tab.sep":           "bg:#16213e #444466",

    "frame":             "#444466",
    "frame.label":       "#7c83ff bold",
    "shadow":            "bg:#1a1a2e",

    "input-prompt":      "#7c83ff bold",

    "bottom-bar":        "bg:#16213e #8892b0",
    "bottom-bar.key":    "bg:#16213e #7c83ff bold",
})


class RoomManager:

    def __init__(self, username):
        self.username = username
        self.rooms = {}
        self.unread = {}
        self.active = None

    def ensure_room(self, user):
        if user not in self.rooms:
            self.rooms[user] = []
            self.unread[user] = 0

    def switch_to(self, user):
        self.ensure_room(user)
        self.active = user
        self.unread[user] = 0

    def add_system(self, user, text):
        ts = datetime.now().strftime("%H:%M:%S")
        self.ensure_room(user)
        self.rooms[user].append(f"  [{ts}]  {text}")

    def add_chat(self, user, sender, text):
        ts = datetime.now().strftime("%H:%M")
        self.ensure_room(user)
        if sender == self.username:
            self.rooms[user].append(f"  {ts}  you \u203a {text}")
        else:
            self.rooms[user].append(f"  {ts}  {sender} \u203a {text}")

        if user != self.active:
            self.unread[user] = self.unread.get(user, 0) + 1

    def get_history(self, user):
        if user not in self.rooms:
            return ""
        return "\n".join(self.rooms[user]) + "\n"

    def get_active_history(self):
        if self.active is None:
            return ""
        return self.get_history(self.active)

    def room_list(self):
        result = []
        for user in self.rooms:
            result.append((user, self.unread.get(user, 0), user == self.active))
        return result


def main():

    if len(sys.argv) >= 2:
        username = sys.argv[1]
    else:
        username = input("Enter your username (default: anna): ").strip() or "anna"

    host = sys.argv[2] if len(sys.argv) >= 3 else "127.0.0.1"
    port = int(sys.argv[3]) if len(sys.argv) >= 4 else 5050


    state = {"connected": False}
    rooms = RoomManager(username)

    global_log = []


    history_area = TextArea(
        text="",
        read_only=True,
        focusable=False,
        scrollbar=True,
        wrap_lines=True,
    )
    input_field = TextArea(
        height=1,
        prompt=[("class:input-prompt", " \u203a ")],
        multiline=False,
        focus_on_click=True,
    )

    def set_history_text(text: str):
        history_area.read_only = False
        history_area.buffer.document = Document(
            text=text, cursor_position=len(text)
        )
        history_area.read_only = True

    def refresh_view():
        if rooms.active is None:

            content = "\n".join(global_log) + "\n" if global_log else ""
            set_history_text(content)
        else:
            set_history_text(rooms.get_active_history())

    def global_sys_msg(text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        global_log.append(f"  [{ts}]  {text}")


    global_log.append("  \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
    global_log.append("  \u2551          \uf023  E2EE Encrypted Chat  \uf023           \u2551")
    global_log.append("  \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d")
    global_log.append("")
    global_sys_msg(f"Logged in as: {username}")
    global_sys_msg("Type /chat <user> to start a conversation.")
    global_sys_msg("Type /quit or Ctrl-C to exit.")
    global_log.append("")
    refresh_view()


    def get_status_bar():
        conn = ("class:status.secure", " \uf111 CONNECTED ") if state["connected"] else ("class:status.warning", " \uf10c DISCONNECTED ")
        active = ("class:status.key", f" \uf075 {rooms.active} ") if rooms.active else ("class:status", " no active chat ")
        return [
            ("class:status", " E2EE "),
            ("class:status", "\u2502"),
            conn,
            ("class:status", "\u2502"),
            active,
            ("class:status", " " * 120),
        ]


    def get_tab_bar():
        room_list = rooms.room_list()
        if not room_list:
            return [("class:tab", "  no open chats" + " " * 120)]

        parts = [("class:tab", " ")]
        for i, (user, unread, is_active) in enumerate(room_list):
            if i > 0:
                parts.append(("class:tab.sep", " \u2502 "))
            if is_active:
                parts.append(("class:tab.active", f" \uf075 {user} "))
            elif unread > 0:
                parts.append(("class:tab.unread", f" \uf0f3 {user} ({unread}) "))
            else:
                parts.append(("class:tab", f"  {user} "))
        parts.append(("class:tab", " " * 120))
        return parts


    def get_bottom_bar():
        return [
            ("class:bottom-bar.key", " /chat <user> "),
            ("class:bottom-bar", " switch room  "),
            ("class:bottom-bar.key", " /quit "),
            ("class:bottom-bar", " exit  "),
            ("class:bottom-bar.key", " Ctrl-C "),
            ("class:bottom-bar", " quit  "),
            ("class:bottom-bar", " " * 120),
        ]


    status_bar = Window(
        content=FormattedTextControl(get_status_bar),
        height=1,
        style="class:status",
    )
    tab_bar = Window(
        content=FormattedTextControl(get_tab_bar),
        height=1,
        style="class:tab",
    )
    bottom_bar = Window(
        content=FormattedTextControl(get_bottom_bar),
        height=1,
        style="class:bottom-bar",
    )
    separator = Window(height=1, char="\u2500", style="class:frame")

    root = HSplit([
        status_bar,
        tab_bar,
        Frame(
            history_area,
            title=" messages ",
            style="class:frame",
        ),
        separator,
        input_field,
        bottom_bar,
    ])


    kb = KeyBindings()

    @kb.add("c-c")
    def _(event):
        event.app.exit()


    app = Application(
        layout=Layout(root, focused_element=input_field),
        key_bindings=kb,
        style=STYLE,
        full_screen=True,
        mouse_support=True,
    )


    def on_message(msg):
        if isinstance(msg, dict):
            sender = msg.get("sender", "?")
            content = msg.get("content", "")

            rooms.add_chat(sender, sender, content)

            if rooms.active == sender:
                refresh_view()
        else:
            text = str(msg)

            if rooms.active:
                rooms.add_system(rooms.active, text)
                refresh_view()
            else:
                global_sys_msg(text)
                refresh_view()
        app.invalidate()


    def accept(buff):
        text = input_field.text.strip()
        if not text:
            return

        if text.startswith("/quit"):
            app.exit()

        elif text.startswith("/chat "):
            target = text.split(" ", 1)[1].strip()
            if not target:
                global_sys_msg("Usage: /chat <username>")
                refresh_view()
            elif target == username:
                global_sys_msg("You cannot chat with yourself.")
                refresh_view()
            else:
                rooms.switch_to(target)

                if len(rooms.rooms[target]) == 0:
                    rooms.add_system(target, f"\u2501\u2501\u2501 Secure session with {target} \u2501\u2501\u2501")
                refresh_view()
                input_field.text = ""
                app.invalidate()
                return

        else:
            if rooms.active:
                rooms.add_chat(rooms.active, username, text)
                motor._send_message(rooms.active, text)
                refresh_view()
            else:
                global_sys_msg("No active chat. Use /chat <user> first.")
                refresh_view()

        input_field.text = ""
        app.invalidate()

    input_field.accept_handler = accept


    motor = ChatClientCore(username, on_message, host, port)

    try:
        motor.connect()
        state["connected"] = True
    except Exception as e:
        global_sys_msg(f"Connection failed: {e}")
        refresh_view()

    app.run()


if __name__ == "__main__":
    main()
