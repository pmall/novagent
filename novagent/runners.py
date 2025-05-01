import asyncio
from novagent.session import NovagentSession


class DummyRunner:
    def __init__(self, session: NovagentSession):
        self.session = session

    def run(self, task: str) -> str | None:
        return asyncio.run(self._run(task))

    async def _run(self, task: str) -> str | None:
        async for _ in self.session.arun(task):
            pass
        return self.session.final_answer_value()


class PrintRunner:
    def __init__(self, session: NovagentSession):
        self.session = session

    def run(self, task: str) -> str | None:
        return asyncio.run(self._run(task))

    async def _run(self, task: str) -> str | None:
        async for message in self.session.arun(task):
            print(message)
        return self.session.final_answer_value()
