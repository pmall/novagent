from litellm import completion


class LiteLLMModel:
    def __init__(
        self, model_id: str, api_key: str | None = None, api_base: str | None = None
    ):
        self.model_id = model_id
        self.api_key = api_key
        self.api_base = api_base

    def __call__(self, messages: list[dict]) -> str:
        response = completion(
            model=self.model_id, api_key=self.api_key, messages=messages
        )

        return response.choices[0].message.content
