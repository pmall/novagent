from litellm import completion


class LiteLLMModel:
    def __init__(
        self, model_id: str, api_key: str | None = None, api_base: str | None = None
    ):
        self.model_id = model_id
        self.api_key = api_key
        self.api_base = api_base

    def __call__(self, messages: list[dict]) -> tuple[str, int | None, int | None]:
        response = completion(
            model=self.model_id, api_key=self.api_key, messages=messages
        )

        message = response.choices[0].message.content

        usage = response.get("usage", {})

        return (
            message,
            usage.get("prompt_tokens", None),
            usage.get("completion_tokens", None),
        )
