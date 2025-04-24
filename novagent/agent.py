import re
from pathlib import Path
from typing import Callable
from string import Template
from context import PythonContext
from loggers import LogLevel, CliLogger


class Novagent:
    def __init__(
        self,
        model: Callable[[list[dict]], str],
        context: PythonContext | None = None,
        authorized_imports: list[str] = [],
        logger: Callable[[str, str | None], None] | None = None,
        log_level: LogLevel | None = LogLevel.NORMAL,
    ):
        self.model = model

        self.context = context or PythonContext()
        self.log = logger or CliLogger(level=log_level)

        self.system_prompt = self._build_system_prompt(authorized_imports)

        self.clear()

    def _build_system_prompt(self, authorized_imports: list[str]):
        system_prompt_tpl_path = Path(__file__).parent / "system_prompt.txt"

        with open(system_prompt_tpl_path) as f:
            system_prompt_tpl = f.read()

        return (
            Template(system_prompt_tpl)
            .substitute(authorized_imports=authorized_imports)
            .strip()
        )

    def _add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def _add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def _call_model(self) -> str:
        response = self.model(self.messages)

        if not response:
            raise ValueError("No response from model.")

        return response

    def _extract_thought_and_code(self, text: str) -> tuple[str, str | None]:
        parts_match = re.match(r"(.*?)```py(.*?)<end_code>", text, re.DOTALL)

        if not parts_match:
            return text, None

        thought = parts_match.group(1).strip()
        code = parts_match.group(2).rstrip("`").strip()

        return thought, code

    def update_system_prompt(self, updater: Callable[[str, list[str]], str]):
        self.system_promp = updater(self.system_promp, self.authorized_imports)

        if not isinstance(self.system_promp, str):
            raise ValueError("System prompt updater must return a string.")

        self.clear()

    def clear(self):
        self.nsteps = 0
        self.messages = [
            {"role": "system", "content": self.system_prompt},
        ]

    def run(self, task: str) -> str:
        self.context.clear_final_answer()
        self._add_user_message(f"Task: {task}")

        while not self.context.has_final_answer:
            self.nsteps += 1

            self.log(f"Step: {self.nsteps}", "info")

            response = self._call_model()

            thought, code = self._extract_thought_and_code(response)

            if not code:
                self.log(thought, "thought")
                self.log("agent did not produced code.", "error")
                continue

            self.log(thought, "thought")
            self.log(code, "code")

            self._add_assistant_message(thought + "\n" + code)

            out, err = self.context.run(code)

            if self.context.has_final_answer:
                self.log(self.context.final_answer_value)
                break

            if len(out) > 0:
                self.log(out, "output")

            if len(err) > 0:
                self.log(err, "error")

            self._add_user_message(f"Observation:\n{out + err}")

        self.log(self.context.final_answer_value, "final")

        return self.context.final_answer_value
