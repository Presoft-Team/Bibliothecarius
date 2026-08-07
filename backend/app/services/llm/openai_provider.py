import openai

from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self._client = openai.OpenAI(api_key=api_key)

    def generate(self, messages: list[ChatMessage], system_prompt: str, params: dict) -> str:
        payload_messages = [{"role": "system", "content": system_prompt}] + [
            {"role": m.role, "content": m.content} for m in messages
        ]
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=payload_messages,
                temperature=params.get("temperature", 0.7),
            )
            return response.choices[0].message.content
        except Exception as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc
