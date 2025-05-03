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

    # ANSI color codes and MessageType to color mapping
    COLORS = {
        "RESET": "\033[0m",
        "RED": "\033[31m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "BLUE": "\033[34m",
        "GREY": "\033[90m",
        "WHITE": "\033[37m",
    }

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
        self.CODE_START = "```py"
        self.CODE_END = "```"

    def run(self, task: str) -> str | None:
        """Run the task and return the final answer."""
        return asyncio.run(self._run(task))

    async def _run(self, task: str) -> str | None:
        """Run the task asynchronously, processing messages as they come in."""
        async for message in self.session.arun(task):
            # Handle step transitions
            if message.step != self.current_step:
                self._print_step_separator()
                self.current_step = message.step
                self.current_type = None
                self.in_code_block = False

            # Handle message type transitions
            if message.type != self.current_type:
                self._print_message_type_header(message.type)
                self.current_type = message.type

            # Print message content with appropriate styling
            if message.type == MessageType.AGENT:
                self._print_agent_content(message.content)
            else:
                self._print_colored_content(
                    message.content, self.TYPE_COLORS[message.type], add_newline=True
                )

        return self.session.final_answer_value()

    def _print_step_separator(self):
        """Print a separator line between steps."""
        separator = "================================================================================"
        self._print_colored_content(separator, self.COLORS["GREY"], add_newline=True)

    def _print_message_type_header(self, message_type):
        """Print the message type header."""
        if self.current_type == MessageType.AGENT:
            self._print_with_delay("\n")

        header = f"[{message_type.name}]"
        self._print_colored_content(
            header, self.TYPE_COLORS[message_type], add_newline=True
        )

    def _print_colored_content(self, content, color, add_newline=False):
        """Print content with specified color."""
        text = f"{color}{content}{self.COLORS['RESET']}"
        if add_newline:
            text += "\n"
        self._print_with_delay(text)

    def _print_agent_content(self, content):
        """Handle agent messages with special processing for code blocks."""
        if self.in_code_block:
            self._handle_content_in_code_block(content)
        elif self.CODE_START in content:
            self._handle_content_with_code_block_start(content)
        else:
            # Regular content without code blocks
            self._print_colored_content(content, self.TYPE_COLORS[MessageType.AGENT])

    def _handle_content_in_code_block(self, content):
        """Handle content when we're already inside a code block."""
        if self.CODE_END in content:
            # This chunk contains the end of a code block
            before_end, after_end = content.split(self.CODE_END, 1)

            # Print code content in yellow
            self._print_colored_content(before_end, self.COLORS["YELLOW"])

            # Print end marker in yellow
            self._print_colored_content(self.CODE_END, self.COLORS["YELLOW"])

            # Print content after code block in white
            if after_end:
                self._print_colored_content(
                    after_end, self.TYPE_COLORS[MessageType.AGENT]
                )

            # Exit code block mode
            self.in_code_block = False
        else:
            # Still in a code block, print everything in yellow
            self._print_colored_content(content, self.COLORS["YELLOW"])

    def _handle_content_with_code_block_start(self, content):
        """Handle content that contains the start of a code block."""
        parts = content.split(self.CODE_START, 1)
        before_code = parts[0]
        after_start = parts[1]

        # Print content before code block if any, ensuring proper spacing
        if before_code:
            before_code = before_code.rstrip()
            if before_code:
                self._print_colored_content(
                    before_code, self.TYPE_COLORS[MessageType.AGENT], add_newline=True
                )

        # Print code start marker in yellow
        self._print_colored_content(self.CODE_START, self.COLORS["YELLOW"])

        # Handle the rest of the content
        if self.CODE_END in after_start:
            # Code block ends in same chunk
            code_parts = after_start.split(self.CODE_END, 1)
            code_content = code_parts[0]
            after_code = code_parts[1] if len(code_parts) > 1 else ""

            # Print code content in yellow
            self._print_colored_content(code_content, self.COLORS["YELLOW"])

            # Print end marker in yellow
            self._print_colored_content(self.CODE_END, self.COLORS["YELLOW"])

            # Print content after code block in white
            if after_code:
                self._print_colored_content(
                    after_code, self.TYPE_COLORS[MessageType.AGENT]
                )
        else:
            # Code block continues beyond this chunk
            self._print_colored_content(after_start, self.COLORS["YELLOW"])
            self.in_code_block = True

    def _print_with_delay(self, text):
        """Print text character by character with a small delay between each character."""
        for char in text:
            print(char, end="", flush=True)
            time.sleep(self.char_delay)
