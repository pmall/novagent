from typing import Callable, Any
from novagent.context import PythonContext
from novagent.session import NovagentSession
from novagent.runners import DummyRunner, PrintRunner
from novagent.system_prompt import default_system_prompt_template


class NovagentConfig:
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
        model: Callable[[list[dict]], Any],
        context: PythonContext | None = None,
        authorized_imports: list[str] = [],
        extra_instructions: str | None = None,
        system_prompt_template: Callable[[list[str], list[str], list[str]], str] = None,
    ):
        self.model = model
        self.context = context or PythonContext()

        self.authorized_imports = (
            authorized_imports or NovagentConfig.DEFAULT_AUTHORIZED_IMPORTS
        )

        self.system_prompt = (
            system_prompt_template(self.authorized_imports, [], [])
            if system_prompt_template
            else default_system_prompt_template(
                extra_instructions, self.authorized_imports, [], []
            )
        )

    def session(self):
        return NovagentSession(self.model, self.context, self.system_prompt)

    def dummy(self):
        return DummyRunner(self.session())

    def print(self):
        return PrintRunner(self.session())
