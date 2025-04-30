import re
from typing import Callable
from context import PythonContext
from outputs import MessageType, DummyOutput
from system_prompt import END_CODE_TAG, default_system_prompt_template


class Novagent:
    DEFAULT_AUTHORIZED_IMPORTS = [
        "os",
        "sys",
        "math",
        "re",
        "json",
        "csv",
        "datetime",
    ]

    def __init__(
        self,
        model: Callable[[list[dict]], str | tuple[str, int | None, int | None]],
        context: PythonContext | None = None,
        output: Callable[[str, str | None], None] | None = None,
        authorized_imports: list[str] = [],
        extra_instructions: str | None = None,
        system_prompt_template: Callable[[list[str], list[str], list[str]], str] = None,
    ):
        self.model = model
        self.context = context or PythonContext()
        self.output = output or DummyOutput()

        self.authorized_imports = (
            authorized_imports or Novagent.DEFAULT_AUTHORIZED_IMPORTS
        )

        self.system_prompt = (
            system_prompt_template(self.authorized_imports, [], [])
            if system_prompt_template
            else default_system_prompt_template(
                extra_instructions, self.authorized_imports, [], []
            )
        )

        # init stateful params
        self.clear()

    def clear(self):
        self.nsteps = 0
        self.in_tokens = 0
        self.out_tokens = 0
        self.messages = [
            {"role": "system", "content": self.system_prompt},
        ]

    def run(self, task: str) -> str:
        # clear the last final answer when run is called again.
        self.context.clear_final_answer()

        # start by adding the task in the message list.
        self.output(f"Task: {task}", MessageType.INFO)

        self._add_user_message(f"Task: {task}")

        # loop until a final answer.
        while not self.context.has_final_answer:
            # get the model response from the current list of messages.
            message, in_tokens, out_tokens = self._call_model()

            # update the current step info and log it.
            self.nsteps += 1
            self.output(f"Step {self.nsteps}:", MessageType.INFO)

            # try to extract thought and code from the model response.
            thought, code = self._extract_thought_and_code(message)

            if not code:
                self.output(thought, MessageType.THOUGHT)
                self.output("agent did not produced code.", MessageType.ERROR)
                continue

            # handle the produced code.
            self.output(thought, MessageType.THOUGHT)
            self.output(code, MessageType.CODE)

            self._add_assistant_message(f"{thought}\n```py\n{code}\n```{END_CODE_TAG}")

            out, err = self.context.run(code)

            # no final answer yet so we add the produced messages to the list and loop.
            if self.context.has_final_answer:
                self.output(self.context.final_answer_value, MessageType.FINAL)
                self._add_user_message(f"Final:\n{self.context.final_answer_value}")
            else:
                parts = []

                if len(out) > 0:
                    self.output(out, MessageType.OUTPUT)
                    parts.append(out)

                if len(err) > 0:
                    self.output(err, MessageType.ERROR)
                    parts.append(err)

                self._add_user_message(f"Observation:\n{"\n".join(parts)}")

            # log current step tokens consumption.
            if in_tokens:
                self.in_tokens += in_tokens

            if out_tokens:
                self.out_tokens += out_tokens

            self._log_current_tokens()

        return self.context.final_answer_value

    def _call_model(self) -> tuple[str, int | None, int | None]:
        response = self.model(self.messages)

        if isinstance(response, str):
            return response, None, None

        if isinstance(response, tuple) and len(response) == 3:
            message, in_tokens, out_tokens = response
            if (
                isinstance(message, str)
                and (not in_tokens or isinstance(in_tokens, int))
                and (not out_tokens or isinstance(out_tokens, int))
            ):
                return message, in_tokens, out_tokens

        raise ValueError(
            "Model function must return string or tuple[str, int | None, int | None]."
        )

    def _add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def _add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def _extract_thought_and_code(self, text: str) -> tuple[str, str | None]:
        parts_match = re.match(rf"(.*?)```py(.*?)```", text, re.DOTALL)

        if not parts_match:
            return text, None

        thought = parts_match.group(1).strip()
        code = parts_match.group(2).strip()

        return thought, code

    def _log_current_tokens(self):
        if self.in_tokens and not self.out_tokens:
            self.output(
                f"Total tokens {self.in_tokens} (in: {self.in_tokens}  - out: ?)",
                MessageType.INFO,
            )

        if not self.in_tokens and self.out_tokens:
            self.output(
                f"Total tokens {self.out_tokens} (in: ? - out: {self.out_tokens})",
                MessageType.INFO,
            )

        if self.in_tokens and self.out_tokens:
            self.output(
                f"Total tokens {self.in_tokens + self.out_tokens} (in: {self.in_tokens} - out: {self.out_tokens})",
                MessageType.INFO,
            )
