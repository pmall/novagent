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
