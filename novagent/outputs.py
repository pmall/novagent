from enum import Enum


class MessageType(Enum):
    INFO = 0
    THOUGHT = 1
    CODE = 2
    OUTPUT = 3
    ERROR = 4
    FINAL = 5


class DummyOutput:
    def __call__(self, msg, type: MessageType = MessageType.INFO):
        pass


class PrintOutput:
    def __call__(self, msg, type: MessageType = MessageType.INFO):
        print(f"[{type.name}] {msg}")


class CliOutput:
    COLORS = {
        MessageType.INFO: "\033[90m",  # gray
        MessageType.THOUGHT: "\033[97m",  # white
        MessageType.CODE: "\033[93m",  # yellow
        MessageType.OUTPUT: "\033[94m",  # blue
        MessageType.ERROR: "\033[91m",  # red
        MessageType.FINAL: "\033[92m",  # green
    }

    def __init__(self):
        self.reset = "\033[0m"

    def __call__(self, msg, type: MessageType = MessageType.INFO):
        color = self.COLORS.get(type, self.COLORS[MessageType.INFO])

        if type == MessageType.CODE:
            print(f"{color}[{type.name}]\n{msg}{self.reset}")
        else:
            print(f"{color}[{type.name}] {msg}{self.reset}")
