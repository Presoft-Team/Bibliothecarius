import anthropic

from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(self, messages: list[ChatMessage], system_prompt: str, params: dict) -> str:
        try:
            response = self._client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                max_tokens=params.get("max_tokens", 1024),
                temperature=params.get("temperature", 0.7),
            )
            return "".join(block.text for block in response.content if block.type == "text")
        except Exception as exc:
            raise LLMProviderError(f"Anthropic request failed: {exc}") from exc
