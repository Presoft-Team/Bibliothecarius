import google.generativeai as genai

from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError

_ROLE_MAP = {"user": "user", "assistant": "model"}


class GeminiProvider(LLMProvider):
    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self._api_key = api_key

    def generate(self, messages: list[ChatMessage], system_prompt: str, params: dict) -> str:
        if not messages:
            raise LLMProviderError("Gemini requires at least one message")
        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self.model, system_instruction=system_prompt)
        history = [
            {"role": _ROLE_MAP[m.role], "parts": [m.content]} for m in messages[:-1]
        ]
        try:
            chat = model.start_chat(history=history)
            response = chat.send_message(
                messages[-1].content,
                generation_config={"temperature": params.get("temperature", 0.7)},
            )
            return response.text
        except Exception as exc:
            # Catches auth errors, invalid model names, safety blocks (response.text raises
            # ValueError when a response has no candidates), and anything else the SDK throws —
            # GoogleAPIError alone missed most of these and let them surface as raw 500s.
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc
