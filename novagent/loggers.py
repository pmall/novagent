from enum import Enum


class LogLevel(Enum):
    SILENT = 0
    MINIMAL = 1
    NORMAL = 2
    VERBOSE = 3


class CliLogger:
    COLORS = {
        "thought": "\033[97m",  # white
        "code": "\033[93m",  # yellow
        "output": "\033[94m",  # blue
        "error": "\033[91m",  # red
        "final": "\033[92m",  # green
        "info": "\033[90m",  # gray
        "reset": "\033[0m",
    }

    VERBOSITY = {
        "final": LogLevel.SILENT,
        "error": LogLevel.MINIMAL,
        "thought": LogLevel.NORMAL,
        "output": LogLevel.NORMAL,
        "code": LogLevel.VERBOSE,
        "info": LogLevel.VERBOSE,
    }

    def __init__(self, level=LogLevel.NORMAL):
        self.level = level

    def __call__(self, msg, type="info"):
        required_level = self.VERBOSITY.get(type, LogLevel.NORMAL)
        if self.level.value < required_level.value:
            return

        color = self.COLORS.get(type, self.COLORS["info"])
        label = type.upper()
        if type == "code":
            print(f"{color}[{label}]\n{msg}{self.COLORS['reset']}")
        else:
            print(f"{color}[{label}] {msg}{self.COLORS['reset']}")
