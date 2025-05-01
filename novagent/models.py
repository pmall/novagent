from typing import Callable
from litellm import completion
from novagent.loggers import DummyLogger
from novagent.system_prompt import END_CODE_TAG


class ModelWrapper:
    def __init__(
        self, model: Callable[[list[dict]], str | tuple[str, int | None, int | None]]
    ):
        self.model = model

    def __call__(self, messages: list[dict]) -> tuple[str, int | None, int | None]:
        response = self.model(messages)

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

    def __call__(self, messages: list[dict]) -> tuple[str, int | None, int | None]:
        response = completion(
            model=self.model_id,
            api_key=self.api_key,
            api_base=self.api_base,
            messages=messages,
            stop=END_CODE_TAG,
            drop_params=True,
        )

        self.log(messages, response.to_dict())

        message = response.choices[0].message.content

        usage = response.get("usage", {})

        return (
            message,
            usage.get("prompt_tokens", None),
            usage.get("completion_tokens", None),
        )
