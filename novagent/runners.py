import re
import asyncio
from novagent.session import MessageType, NovagentSession


class DummyRunner:
    def __init__(self, session: NovagentSession):
        self.session = session

    def run(self, task: str) -> str | None:
        return asyncio.run(self._run(task))

    async def _run(self, task: str) -> str | None:
        async for _ in self.session.arun(task):
            pass
        return self.session.final_answer_value()


class StdoutRunner:
    def __init__(self, session: NovagentSession):
        self.session = session
        self.current_step = None
        self.current_type = None

    def run(self, task: str) -> str | None:
        return asyncio.run(self._run(task))

    async def _run(self, task: str) -> str | None:
        async for message in self.session.arun(task):
            if message.step != self.current_step:
                print(
                    "================================================================================"
                )
                self.current_type = None
                self.current_step = message.step

            if message.type != self.current_type:
                if self.current_type == MessageType.AGENT:
                    print("")

                print(f"[{message.type.name}]")
                self.current_type = message.type

            print(message.content, end="")

            if message.type != MessageType.AGENT:
                print("")

        return self.session.final_answer_value()


class CliRunner:
    """
    A runner that executes a session and outputs colored messages to the terminal.

    Colors by MessageType:
    - INFO: Grey
    - AGENT: White (Python code blocks are displayed in yellow)
    - OUTPUT: Blue
    - ERROR: Red
    - FINAL: Green
    """

    # ANSI color codes
    COLORS = {
        "RESET": "\033[0m",
        "RED": "\033[31m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "BLUE": "\033[34m",
        "GREY": "\033[90m",
        "WHITE": "\033[37m",
    }

    # MessageType to color mapping
    TYPE_COLORS = {
        MessageType.INFO: COLORS["GREY"],
        MessageType.AGENT: COLORS["WHITE"],
        MessageType.OUTPUT: COLORS["BLUE"],
        MessageType.ERROR: COLORS["RED"],
        MessageType.FINAL: COLORS["GREEN"],
    }

    def __init__(self, session: NovagentSession):
        self.session = session
        self.current_step = None
        self.current_type = None
        self.in_code_block = False

    def run(self, task: str) -> str | None:
        return asyncio.run(self._run(task))

    async def _run(self, task: str) -> str | None:
        async for message in self.session.arun(task):
            if message.step != self.current_step:
                print(
                    self.COLORS["GREY"]
                    + "================================================================================"
                    + self.COLORS["RESET"]
                )
                self.current_type = None
                self.current_step = message.step
                self.in_code_block = False

            if message.type != self.current_type:
                if self.current_type == MessageType.AGENT:
                    print("")

                color = self.TYPE_COLORS.get(message.type, self.COLORS["WHITE"])
                print(f"{color}[{message.type.name}]{self.COLORS['RESET']}")
                self.current_type = message.type

            # Process the content with handling for code blocks
            self._process_content(message.content, message.type)

            # Add newline for non-AGENT messages
            if message.type != MessageType.AGENT:
                print("")

        return self.session.final_answer_value()

    def _process_content(self, content: str, message_type: MessageType):
        """Process content with special handling for code blocks in AGENT messages."""
        if message_type != MessageType.AGENT:
            # For non-AGENT messages, just print with the appropriate color
            color = self.TYPE_COLORS.get(message_type, self.COLORS["WHITE"])
            print(f"{color}{content}{self.COLORS['RESET']}", end="")
            return

        # For AGENT messages, handle code blocks
        code_start = "```py"
        code_end = "```"

        # Check for code block markers in this chunk
        if code_start in content:
            # We found the start of a code block
            parts = content.split(code_start, 1)

            # Print the text before the code block
            print(
                f"{self.TYPE_COLORS[MessageType.AGENT]}{parts[0]}{self.COLORS['RESET']}",
                end="",
            )

            # Print the code start marker
            print(f"{self.COLORS['YELLOW']}{code_start}", end="")

            # Set that we're in a code block
            self.in_code_block = True

            # Process the rest of the content
            self._process_code_content(parts[1])
        elif code_end in content and self.in_code_block:
            # We found the end of a code block
            parts = content.split(code_end, 1)

            # Print the code content
            print(f"{self.COLORS['YELLOW']}{parts[0]}", end="")

            # Print the code end marker
            print(f"{self.COLORS['YELLOW']}{code_end}{self.COLORS['RESET']}", end="")

            # Set that we're no longer in a code block
            self.in_code_block = False

            # Print the text after the code block
            print(
                f"{self.TYPE_COLORS[MessageType.AGENT]}{parts[1]}{self.COLORS['RESET']}",
                end="",
            )
        else:
            # Regular content, or content within a code block
            color = (
                self.COLORS["YELLOW"]
                if self.in_code_block
                else self.TYPE_COLORS[MessageType.AGENT]
            )
            print(f"{color}{content}{self.COLORS['RESET']}", end="")

    def _process_code_content(self, content: str):
        """Process content that comes after a code block start."""
        code_end = "```"

        if code_end in content:
            # The code block ends in the same chunk
            parts = content.split(code_end, 1)

            # Print the code content
            print(f"{self.COLORS['YELLOW']}{parts[0]}", end="")

            # Print the code end marker
            print(f"{self.COLORS['YELLOW']}{code_end}{self.COLORS['RESET']}", end="")

            # Set that we're no longer in a code block
            self.in_code_block = False

            # Print the text after the code block
            print(
                f"{self.TYPE_COLORS[MessageType.AGENT]}{parts[1]}{self.COLORS['RESET']}",
                end="",
            )
        else:
            # The code block continues
            print(f"{self.COLORS['YELLOW']}{content}{self.COLORS['RESET']}", end="")
