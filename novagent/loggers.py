from enum import Enum


class LogLevel(Enum):
    SILENT = 0
    MINIMAL = 1
    NORMAL = 2
    VERBOSE = 3


class LogAction(Enum):
    INFO = 0
    THOUGHT = 1
    CODE = 2
    OUTPUT = 3
    ERROR = 4
    FINAL = 5


LOG_VERBOSITY = {
    LogAction.FINAL: LogLevel.SILENT,
    LogAction.ERROR: LogLevel.MINIMAL,
    LogAction.THOUGHT: LogLevel.NORMAL,
    LogAction.OUTPUT: LogLevel.NORMAL,
    LogAction.CODE: LogLevel.VERBOSE,
    LogAction.INFO: LogLevel.VERBOSE,
}


class DummyLogger:
    def __init__(self, level: LogLevel = LogLevel.NORMAL):
        self.level = level

    def __call__(self, msg, type: LogAction = LogAction.INFO):
        required_level = LOG_VERBOSITY.get(type, LogLevel.NORMAL)
        if self.level.value < required_level.value:
            return

        print(f"[{type.name}] {msg}")


class CliLogger:
    COLORS = {
        LogAction.INFO: "\033[90m",  # gray
        LogAction.THOUGHT: "\033[97m",  # white
        LogAction.CODE: "\033[93m",  # yellow
        LogAction.OUTPUT: "\033[94m",  # blue
        LogAction.ERROR: "\033[91m",  # red
        LogAction.FINAL: "\033[92m",  # green
    }

    def __init__(self, level: LogLevel = LogLevel.NORMAL):
        self.level = level
        self.reset = "\033[0m"

    def __call__(self, msg, type: LogAction = LogAction.INFO):
        required_level = LOG_VERBOSITY.get(type, LogLevel.NORMAL)
        if self.level.value < required_level.value:
            return

        color = self.COLORS.get(type, self.COLORS[LogAction.INFO])

        if type == LogAction.CODE:
            print(f"{color}[{type.name}]\n{msg}{self.reset}")
        else:
            print(f"{color}[{type.name}] {msg}{self.reset}")
