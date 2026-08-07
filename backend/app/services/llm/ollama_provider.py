import httpx

from app.core.config import settings
from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError


class OllamaProvider(LLMProvider):
    def generate(self, messages: list[ChatMessage], system_prompt: str, params: dict) -> str:
        payload_messages = [{"role": "system", "content": system_prompt}] + [
            {"role": m.role, "content": m.content} for m in messages
        ]
        try:
            response = httpx.post(
                f"{settings.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": payload_messages,
                    "stream": False,
                    "options": {"temperature": params.get("temperature", 0.7)},
                },
                timeout=120.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc

        return response.json()["message"]["content"]
