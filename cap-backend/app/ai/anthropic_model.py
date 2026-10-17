import anthropic

from app.ai.errors import AiUnavailable, InvalidModelOutput, ModelRefused
from app.ai.model import SchemaT


class AnthropicModel:
    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        model: str,
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> None:
        self._client = client
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return self._model

    async def ask(self, system: str, prompt: str, schema: type[SchemaT]) -> SchemaT:
        try:
            message = await self._client.messages.parse(
                model=self._model,
                max_tokens=self._max_output_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_format=schema,
                timeout=self._timeout_seconds,
            )
        except anthropic.APIError as error:
            raise AiUnavailable(f"The model call failed: {error}") from error
        if message.stop_reason == "refusal":
            raise ModelRefused("The model declined to answer")
        if message.parsed_output is None:
            raise InvalidModelOutput("The model answer did not match the requested schema")
        return message.parsed_output
