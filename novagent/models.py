from typing import Callable
from litellm import acompletion, stream_chunk_builder
from novagent.loggers import DummyLogger
from novagent.system_prompt import END_CODE_TAG


class LiteLLMModel:
    def __init__(
        self,
        model_id: str,
        api_key: str | None = None,
        api_base: str | None = None,
        logger: Callable[[list[dict], dict], None] | None = None,
    ):
        self.model_id = model_id
        self.api_key = api_key
        self.api_base = api_base
        self.log = logger or DummyLogger()

    async def __call__(self, messages: list[dict]):
        stream = await acompletion(
            model=self.model_id,
            api_key=self.api_key,
            api_base=self.api_base,
            messages=messages,
            stop=END_CODE_TAG,
            stream=True,
            stream_options={"include_usage": True},
            drop_params=True,
        )

        chunks = []

        async for chunk in stream:
            chunks.append(chunk)
            yield chunk

        response = stream_chunk_builder(chunks, messages=messages)

        self.log(messages, response.to_dict())
