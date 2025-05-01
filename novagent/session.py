import re
from enum import Enum
from typing import AsyncIterator, Callable, Any
from novagent.context import PythonContext
from novagent.system_prompt import END_CODE_TAG


class MessageType(Enum):
    INFO = 0
    AGENT = 1
    OUTPUT = 2
    ERROR = 3
    FINAL = 4


class Message:
    def __init__(self, type: MessageType, step: int, content: str):
        self.type = type
        self.step = step
        self.content = content

    def __repr__(self):
        return f"Message({self.type.name}, {self.step}, {self.content})"


class NovagentSession:
    """
    A session that processes a task by generating and executing code using an LLM model.
    This class is designed as an async iterator that yields Message objects.
    """

    def __init__(
        self,
        model: Callable[[list[dict]], Any],
        context: PythonContext,
        system_prompt: str,
    ):
        self.model = model
        self.context = context
        self.nstep = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.messages = [
            {"role": "system", "content": system_prompt},
        ]

    def final_answer_value(self) -> str | None:
        return self.context.final_answer_value

    async def arun(self, task: str) -> AsyncIterator[Message]:
        """
        Run the session on the given task and yield messages as they, self.nstep are produced.
        This is an async generator that can be used in an async for loop.
        """

        # clear the last final answer when run is called again.
        self.context.clear_final_answer()

        # add the task to the message list.
        self._add_user_message(f"Task: {task}")

        # loop until a final answer.
        while not self.context.has_final_answer:
            # update the current step info and yield it.
            self.nstep += 1

            # get model response as a stream and emit it.
            message = ""
            async for agent_message in self._call_model():
                yield agent_message
                message += agent_message.content

            # try to extract thought and code from the model response.
            thought, code = self._extract_thought_and_code(message)

            if not code:
                yield Message(MessageType.ERROR, self.nstep, f"No code produced.")
                break

            # add the assistant message in the list.
            self._add_assistant_message(f"{thought}\n```py\n{code}\n```{END_CODE_TAG}")

            # yield current step sumup.
            yield Message(MessageType.INFO, self.nstep, self._step_sumup())

            # run the produced code.
            out, err = self.context.run(code)

            # build the "user" message and add it to the list.
            parts = []
            observations = []

            if len(out) > 0:
                yield Message(MessageType.OUTPUT, self.nstep, out)
                observations.append(out)

            if len(err) > 0:
                yield Message(MessageType.ERROR, self.nstep, err)
                observations.append(err)

            if len(observations) > 0:
                parts.append(f"Observation:\n{"\n".join(observations)}")

            if self.context.has_final_answer:
                yield Message(
                    MessageType.FINAL, self.nstep, self.context.final_answer_value
                )
                parts.append(f"Final:\n{self.context.final_answer_value}")

            self._add_user_message("\n".join(parts))

    def _add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def _add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    async def _call_model(self) -> AsyncIterator[Message]:
        async for chunk in self.model(self.messages):
            content = chunk.choices[0].delta.content

            usage = chunk.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", None)
            completion_tokens = usage.get("completion_tokens", None)

            if content:
                # Yield each chunk as it arrives
                yield Message(MessageType.AGENT, self.nstep, content)

            if prompt_tokens:
                self.prompt_tokens = self.prompt_tokens + prompt_tokens

            if completion_tokens:
                self.completion_tokens = self.completion_tokens + completion_tokens

    def _extract_thought_and_code(self, text: str) -> tuple[str, str | None]:
        """Try to extract the thought and code parts"""

        parts_match = re.match(rf"(.*?)```py(.*?)```", text, re.DOTALL)

        if not parts_match:
            return text, None

        thought = parts_match.group(1).strip()
        code = parts_match.group(2).strip()

        return thought, code

    def _step_sumup(self) -> str:
        """Get a formatted string with token usage information."""

        base = f"Step {self.nstep}"

        if not self.prompt_tokens and not self.completion_tokens:
            return base

        if self.prompt_tokens and not self.completion_tokens:
            return f"{base} - Total tokens {self.prompt_tokens} (in: {self.prompt_tokens} - out: ?)"

        if not self.prompt_tokens and self.completion_tokens:
            return f"{base} - Total tokens {self.completion_tokens} (in: ? - out: {self.completion_tokens})"

        return f"{base} - Total tokens {self.prompt_tokens + self.completion_tokens} (in: {self.prompt_tokens} - out: {self.completion_tokens})"
