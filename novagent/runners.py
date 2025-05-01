import time
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

    Features:
    - Character-by-character printing with configurable delay to simulate text generation
    - Color-coded output by message type
    - Special highlighting for Python code blocks

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

    def __init__(self, session: NovagentSession, char_delay=0.001):
        """
        Initialize the CliRunner.

        Args:
            session (NovagentSession): The novagent session to run
            char_delay (float): Delay in seconds between printing each character (default: 1ms)
        """
        self.session = session
        self.current_step = None
        self.current_type = None
        self.in_code_block = False
        self.char_delay = char_delay

    def run(self, task: str) -> str | None:
        return asyncio.run(self._run(task))

    async def _run(self, task: str) -> str | None:
        async for message in self.session.arun(task):
            if message.step != self.current_step:
                self._print_with_delay(
                    self.COLORS["GREY"]
                    + "================================================================================"
                    + self.COLORS["RESET"]
                    + "\n"
                )
                self.current_type = None
                self.current_step = message.step
                self.in_code_block = False

            if message.type != self.current_type:
                if self.current_type == MessageType.AGENT:
                    self._print_with_delay("\n")

                color = self.TYPE_COLORS.get(message.type, self.COLORS["WHITE"])
                self._print_with_delay(
                    f"{color}[{message.type.name}]{self.COLORS['RESET']}\n"
                )
                self.current_type = message.type

            # Special handling for AGENT messages
            if message.type == MessageType.AGENT:
                # Handle potential code blocks in the content
                self._handle_agent_content(message.content)
            else:
                # For non-AGENT messages, just print with the appropriate color
                color = self.TYPE_COLORS.get(message.type, self.COLORS["WHITE"])
                self._print_with_delay(
                    f"{color}{message.content}{self.COLORS['RESET']}\n"
                )

        return self.session.final_answer_value()

    def _handle_agent_content(self, content: str):
        """Handle agent messages with special processing for code blocks."""
        code_start = "```py"
        code_end = "```"

        # Look for code block markers in the content
        if code_start in content:
            # Split at code block start and process each part
            before_code, after_start = content.split(code_start, 1)

            # Print content before code block
            if before_code:
                self._print_with_delay(
                    f"{self.TYPE_COLORS[MessageType.AGENT]}{before_code}{self.COLORS['RESET']}"
                )

            # Print code start marker
            self._print_with_delay(f"{self.COLORS['YELLOW']}{code_start}")

            # Check if code block ends in same chunk
            if code_end in after_start:
                code_content, after_code = after_start.split(code_end, 1)
                # Print code content and end marker
                self._print_with_delay(
                    f"{self.COLORS['YELLOW']}{code_content}{code_end}{self.COLORS['RESET']}"
                )
                # Print content after code block
                if after_code:
                    self._print_with_delay(
                        f"{self.TYPE_COLORS[MessageType.AGENT]}{after_code}{self.COLORS['RESET']}"
                    )
            else:
                # Code block continues beyond this chunk
                self._print_with_delay(
                    f"{self.COLORS['YELLOW']}{after_start}{self.COLORS['RESET']}"
                )
                self.in_code_block = True

        elif code_end in content and self.in_code_block:
            # This chunk contains the end of a code block
            before_end, after_end = content.split(code_end, 1)

            # Print code content and end marker
            self._print_with_delay(
                f"{self.COLORS['YELLOW']}{before_end}{code_end}{self.COLORS['RESET']}"
            )

            # Print content after code block
            if after_end:
                self._print_with_delay(
                    f"{self.TYPE_COLORS[MessageType.AGENT]}{after_end}{self.COLORS['RESET']}"
                )

            # We're no longer in a code block
            self.in_code_block = False

        else:
            # Regular content or content within a code block
            color = (
                self.COLORS["YELLOW"]
                if self.in_code_block
                else self.TYPE_COLORS[MessageType.AGENT]
            )
            self._print_with_delay(f"{color}{content}{self.COLORS['RESET']}")

    def _print_with_delay(self, text):
        """Print text character by character with a small delay between each character."""
        for char in text:
            print(char, end="", flush=True)
            time.sleep(self.char_delay)
